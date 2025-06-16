function Get-BicepParams($path) {
    $result = az bicep build-params -f $path --stdout
    if ($LASTEXITCODE -eq 0) {
        return (($result | ConvertFrom-Json).parametersJson | ConvertFrom-Json).parameters.PSObject.Properties | ForEach-Object -begin {$h=@{}} -process {$h."$($_.Name)" = $_.Value.value} -end {$h}
    }
    else {
        Write-Error -Message "Error in .bicepparams file" -ErrorAction Stop
    }
}

function Get-JsonParams($path) {
    return (Get-Content $path | ConvertFrom-Json)
}

$secretParameters = Get-JsonParams ./secrets.json

function Get-SecretParameter($key) {
    return $secretParameters.$key
}

function Get-SecretParametersStringJoinedBySpaceExceptResourceGroup {
    return $secretParameters.PSObject.Properties | Where-Object { $_.Name -ne "resourceGroup" } | ForEach-Object { "$($_.Name)=`"$($_.Value)`"" }
}

$resourceGroup = Get-SecretParameter resourceGroup
if ($null -eq $resourceGroup) {
    "Create a secrets.json file that contains the resource group name that you want to maintain using AzureUtil.ps1:"
    "{"
    "`t""resourceGroup"": ""my-resource-group"""
    "}"
    "If deploying a new resource group, also provide all secrets marked with @secure in template.bicep."
    return
}
$env:RESOURCE_PREFIX = $resourceGroup

$parameters = Get-BicepParams ./template.bicepparam

function Get-FromParameters($key) {
    return $parameters.$key
}

$registry = Get-FromParameters containerRegistryName
$apiImageName = Get-FromParameters apiImageName
$tileserverImageName = Get-FromParameters tileserverImageName
$uiImageName = Get-FromParameters uiImageName
$apiWebAppName = Get-FromParameters apiWebAppName
$tileserverWebAppName = Get-FromParameters tileserverWebAppName
$uiWebAppName = Get-FromParameters uiWebAppName
$db = Get-FromParameters dbServerName
$dbAdminUser = Get-FromParameters dbAdminUsername
$dbUser = Get-FromParameters dbUsername
$dbDatabase = Get-FromParameters dbName
$storage = Get-FromParameters storageAccountName
$keyvault = Get-FromParameters keyvaultName
$sshPort = 59123

function Test-NetConnectionFaster($Addr, [int] $Port) {
    $TCPClient = [System.Net.Sockets.TcpClient]::new()
    $result = $TCPClient.ConnectAsync($Addr, $Port).Wait(100)
    $TCPClient.Close()
    return $result
}
function Open-AzureWebAppSshConnection($webApp) {
    $command = "az webapp create-remote-connection --resource-group $resourceGroup --name $webApp -p $sshPort"
    $job = Start-Job -ScriptBlock { Invoke-Expression $using:command }
    return $job.Id
}
function Test-AzureWebAppSshConnection {
    return Test-NetConnectionFaster 127.0.0.1 $sshPort
}
function Open-AzureWebAppSsh($webApp) {
    "Connecting to Azure WebApp... if this stalls, might need to run 'AzureUtil config ENABLE_SSH=true'"
    $jobId = Open-AzureWebAppSshConnection $webApp
    ssh-keygen -R [localhost]:$sshPort >nul 2>&1
    do {
        Start-Sleep -Milliseconds 10
    } until (Test-AzureWebAppSshConnection)
    "Connected, establishing SSH terminal. The password is 'Docker!'"
    ssh root@localhost -p $sshPort -o StrictHostKeyChecking=no
    Stop-Job $jobId
}

function Open-AzurePostgresDb {
    "Connecting to db..."
    $env:PGPASSWORD = Get-SecretParameter dbPassword
    psql -h "$db.postgres.database.azure.com" -U $dbUser -d $dbDatabase
    "Done"
}

function Import-AzurePostgresDbDump($dumpFile) {
    "Importing db dump..."
    $dbPassword = Get-SecretParameter dbPassword
    $env:PGPASSWORD = Get-SecretParameter dbAdminPassword
    psql -h "$db.postgres.database.azure.com" -U $dbAdminUser -d $dbDatabase -c "CREATE USER ""$dbUser"" WITH ENCRYPTED PASSWORD '0Z2m5FmhYiMN4OwtOYg5QBt7Qd7NZpa8sLiM51PQHlRDzQnw'; ALTER USER ""$dbUser"" CREATEDB; GRANT ""$dbUser"" TO $dbAdminUser; GRANT ALL ON SCHEMA public TO ""$dbUser"";"
    psql -h "$db.postgres.database.azure.com" -U $dbAdminUser -d $dbDatabase -f $dumpFile
    "Done"
}

function Show-FilesInFileshare($fileshare, $path) {
    if ($path) {
        az storage file list --share-name $fileshare --account-name $storage --query [*].name --account-key (az storage account keys list -g $resourceGroup -n $storage --query [0].value) --path $path
    }
    else {
        az storage file list --share-name $fileshare --account-name $storage --query [*].name --account-key (az storage account keys list -g $resourceGroup -n $storage --query [0].value)
    }
}

function Copy-FilesToFileshare($fileshare, $paths) {
    foreach ($path in $paths) {
        if ($path -match "=") {
            $parts = $path -split "="
            $source = $parts[0]
            $dest = $parts[1]
        }
        else {
            $source = $path
            $dest = ""
        }
        az storage copy -s $source -d https://$storage.file.core.windows.net/$fileshare/$dest --recursive --account-key (az storage account keys list -g $resourceGroup -n $storage --query [0].value)
    }
}

function Show-AzureWebAppLog($webApp) {
    az webapp log tail --resource-group $resourceGroup --name $webApp
}

function Get-SecretFromKeyvault($secretName) {
    return az keyvault secret show --vault-name $keyvault -n $secretName -o tsv --query value
}

function Invoke-AzureWebAppConfig($webApp, $commandOrConfigs) {
    function Parse($value) {
        $secretName = [regex]::Match($value, 'SecretName=(\w+)').Groups[1].Value
        if ($secretName) {
            return Get-SecretFromKeyvault $secretName
        }
        else {
            return $value
        }
    }

    if ($null -eq $commandOrConfigs) {
        az webapp config appsettings list --resource-group $resourceGroup --name $webApp | ConvertFrom-Json | Sort-Object -Property name | ForEach-Object { "$($_.name)=$(Parse($_.value))" }
    }
    elseif ($commandOrConfigs[0] -eq "delete") {
        az webapp config appsettings delete --resource-group $resourceGroup --name $webApp --setting-names ($commandOrConfigs | Select-Object -Skip 1)
    }
    else {
        az webapp config appsettings set --resource-group $resourceGroup --name $webApp --settings $commandOrConfigs
    }
}

function Invoke-BuildAzureContainerImage($image, $path = ".") {
    az acr build --resource-group $resourceGroup --registry $registry --image $image $path
}

function Invoke-ImportAzureContainerImage($image, $source) {
    az acr import --resource-group $resourceGroup --name $registry --source $source --image $image
}

function Get-WebAppName($webApp) {
    switch ($webApp) {
        "api" { $apiWebAppName }
        "tileserver" { $tileserverWebAppName }
        "ui" { $uiWebAppName }
        Default { $null }
    }
}

function Get-ImageName($webApp) {
    switch ($webApp) {
        "api" { $apiImageName }
        "tileserver" { $tileserverImageName }
        "ui" { $uiImageName }
        Default { $null }
    }
}

function Get-WebAppFileshare($webApp) {
    switch ($webApp) {
        "apifiles" { 'api-files' }
        "apidata" { 'api-data' }
        "tileserver" { 'tileserver-data' }
        Default { $null }
    }
}

function Show-Usage {
    "Usage:"
    ""
    "./AzureUtil deploy"
    "`tCreate a new resource group and deploy resources to it using template.bicep and parameters from template.bicepparam, and from secrets.json which is excluded from version control and can thus contain secrets"
    "./AzureUtil build [api|tileserver|ui] [path]"
    "`tBuild a new image in the WebApp's Azure container registry"
    "./AzureUtil importimage [api|tileserver|ui] [docker.io/helsinki/tileserver-gl]"
    "`tImport an online image in the WebApp's Azure container registry"
    "./AzureUtil log [api|tileserver|ui]"
    "`tView the WebApp's log stream"
    "./AzureUtil ssh [api|tileserver|ui]"
    "`tAccess the WebApp's SSH, assuming one is set up in docker-entrypoint"
    "./AzureUtil db"
    "`tAccess Azure Postgres DB Flexible Server instance with psql"
    "./AzureUtil dbimport [dump.sql]"
    "`tImport a DB dump file to Azure Postgres DB Flexible Server instance with psql"
    "./AzureUtil config [api|tileserver|ui]"
    "`tShow the WebApp's environment variables in a .env file format, retrieving Key Vault secret references"
    "./AzureUtil config [api|tileserver|ui] setting1=value1 setting2=value2 ..."
    "`tAssign the given values in the WebApp's environment variables"
    "./AzureUtil config delete [api|tileserver|ui] setting1 setting2 ..."
    "`tDelete the given keys from the WebApp's environment variables"
    "./AzureUtil files [apifiles|apidata|tileserver|ui] [path]"
    "`tList files in the Azure Storage fileshare using a path"
    "./AzureUtil copyfiles [apifiles|apidata|tileserver|ui] [d:/turku/remote/servicemap-test/bew/staticroot]"
    "`tCopy files to the Azure Storage fileshare"
    "./AzureUtil param [dbName]"
    "`tShow a config value from parameters.json"
}

switch ($args[0]) {
    "deploy" {
        az group create -l swedencentral -n $resourceGroup
        az deployment group create --template-file ./template.bicep --parameters 'template.bicepparam' --parameters (Get-SecretParametersStringJoinedBySpaceExceptResourceGroup) --resource-group $resourceGroup @($args | Select-Object -Skip 1)
        return
    }
    "build" {
        $imageName = Get-ImageName $args[1]
        if ($null -ne $imageName) {
            Invoke-BuildAzureContainerImage $imageName $args[2]
        }
        else { Show-Usage }
        return
    }
    "importimage" {
        $imageName = Get-ImageName $args[1]
        if ($null -ne $imageName) {
            Invoke-ImportAzureContainerImage $imageName $args[2]
        }
        else { Show-Usage }
        return
    }
    "log" {
        $webAppName = Get-WebAppName $args[1]
        if ($null -ne $webAppName) {
            Show-AzureWebAppLog $webAppName
        }
        else { Show-Usage }
        return
    }
    "ssh" {
        $webAppName = Get-WebAppName $args[1]
        if ($null -ne $webAppName) {
            Open-AzureWebAppSsh $webAppName
        }
        else { Show-Usage }
        return
    }
    "db" {
        Open-AzurePostgresDb
        return
    }
    "dbimport" {
        Import-AzurePostgresDbDump $args[1]
        return
    }
    "config" {
        $webAppName = Get-WebAppName $args[1]
        if ($null -ne $webAppName) {
            Invoke-AzureWebAppConfig $webAppName ($args | Select-Object -Skip 2)
        }
        else { Show-Usage }
        return
    }
    "files" {
        $fileshare = Get-WebAppFileshare $args[1]
        if ($null -ne $fileshare) {
            Show-FilesInFileshare $fileshare $args[2]
        }
        else { Show-Usage }
        return
    }
    "copyfiles" {
        $fileshare = Get-WebAppFileshare $args[1]
        if ($null -ne $fileshare) {
            Copy-FilesToFileshare $fileshare ($args | Select-Object -Skip 2)
        }
        else { Show-Usage }
        return
    }
    "param" {
        Write-Output (Get-FromParameters $args[1])
        return
    }
    Default {
        Show-Usage
    }
}