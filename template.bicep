param location string = resourceGroup().location
param apiImageName string
param apiInternalUrl string
param apiUrl string
param tileserverImageName string
param tileserverUrl string
param uiImageName string
@description('API WebApp name. Must be globally unique')
param apiWebAppName string
@description('Tileserver WebApp name. Must be globally unique')
param tileserverWebAppName string
@description('UI WebApp name. Must be globally unique')
param uiWebAppName string
@description('Cache name. Must be globally unique')
param cacheName string
@description('Key vault name. Must be globally unique. Lowercase and numbers only')
@maxLength(24)
@minLength(3)
param keyvaultName string
param serverfarmPlanName string
@description('Storage account name. Must be globally unique. Lowercase and numbers only')
@maxLength(24)
@minLength(3)
param storageAccountName string
param apiOutboundIpName string
param natGatewayName string
param vnetName string
@description('Container registry name. Must be globally unique. Alphanumeric only')
@maxLength(50)
@minLength(5)
param containerRegistryName string
param dbServerName string
param dbName string
param workspaceName string
param appInsightsName string
param dbPostgresExtensions string = 'POSTGIS,HSTORE,PG_TRGM'
param dbAdminUsername string
param dbUsername string
@secure()
param dbAdminPassword string = ''
@secure()
param dbPassword string = ''

// Application specific parameters
@secure()
param secretKey string = ''
// @secure()
// param djangoSuperuserPassword string = ''
@secure()
param digitransitApiKey string = ''
// @secure()
// param emailHostPassword string = ''
@secure()
param geoSearchApiKey string = ''
@secure()
param kuntecKey string = ''
@secure()
param open311ApiKey string = ''
@secure()
param open311InternalApiKey string = ''
@secure()
param open311ServiceCode string = ''
@secure()
param telraamToken string = ''
@secure()
param turkuApiKey string = ''
@secure()
param yitClientSecret string = ''

// Prod
param uiAppSettings object = {
  ACCESSIBILITY_SENTENCE_API: 'https://tpr.hel.fi/kapaesteettomyys/api/v1/accessibility/servicepoints/d26b5f28-41c6-40a3-99f9-a1b762cc8191'
  ACCESSIBLE_MAP_URL: '${tileserverUrl}/styles/high-contrast-map-layer/{z}/{x}/{y}'
  AIR_MONITORING_API: '${apiUrl}/environment_data/api/v1'
  CITIES: 'turku,kaarina,naantali,raisio'
  DIGITRANSIT_API: 'https://api.digitransit.fi/routing/v2/waltti/gtfs/v1'
  DIGITRANSIT_API_KEY: digitransitApiKey
  EVENTS_API: 'https://linkedevents-api.turku.fi/v1' //ei käytössä?
  FEEDBACK_ADDITIONAL_INFO_LINK: 'https://opaskartta.turku.fi/eFeedback/fi/Home/AboutService'
  FEEDBACK_ADDITIONAL_INFO_LINK_EN: 'https://opaskartta.turku.fi/eFeedback/en/Home/AboutService'
  FEEDBACK_ADDITIONAL_INFO_LINK_SV: 'https://opaskartta.turku.fi/eFeedback/sv/Home/AboutService'
  FEEDBACK_IS_PUBLISHED: 'false'
  FEEDBACK_URL: 'https://kehityspalvelukartta-api.turku.fi/open311/'
  INITIAL_MAP_POSITION: '60.451799,22.266414'
  LANG: 'en_US.utf8'
  LC_ALL: 'en_US.UTF-8'
  LC_LANG: 'en_US.UTF-8'
  MAPS: 'servicemap,accessible_map'
  MATOMO_SITE_ID: '7'
  MATOMO_URL: 'https://matomo.turku.fi'
  MOBILITY_PLATFORM_API: apiUrl
  MOBILITY_TEST_API: 'https://liikkumistesti-api.turku.fi/api/v1/postalcoderesult'
  MODE: 'production'
  NODE_ENV: 'production'
  OLD_MAP_LINK_EN: 'https://servicemap.turku.fi/'
  OLD_MAP_LINK_FI: 'https://palvelukartta.turku.fi/'
  OLD_MAP_LINK_SV: 'https://servicekarta.turku.fi/'
  PARKING_SPACES_URL: 'https://parkkiopas.turku.fi/public/v1/parking_area/'
  PARKING_STATISTICS_URL: 'https://parkkiopas.turku.fi/public/v1/parking_area_statistics/'
  PORT: '2048'
  PORTNET_API: 'https://meri.digitraffic.fi/api/port-call/v1'
  PRODUCTION_PREFIX: 'SM'
  RAILWAYS_API: 'https://rata.digitraffic.fi/api/v1'
  REITTIOPAS_URL: 'https://reittiopas.foli.fi/reitti/'
  RESERVATIONS_API: 'https://respa.turku.fi/v1'
  ROADWORKS_API: '${apiUrl}/exceptional_situations/api/v1'
  SERVICE_MAP_URL: '${tileserverUrl}/styles/hel-osm-bright/{z}/{x}/{y}'
  SERVICEMAP_API: '${apiUrl}/api'
  SERVICEMAP_API_VERSION: '/v2'
  SHOW_AREA_SELECTION: 'true'
  SHOW_READ_SPEAKER_BUTTON: 'false'
  SSR_FETCH_TIMEOUT: '2500'
  THEME_PKG: '1'
  USE_PTV_ACCESSIBILITY_API: 'true'
  WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'false'
}
// Test
// param uiAppSettings object = {
//   ACCESSIBILITY_SENTENCE_API: 'https://tpr.hel.fi/kapaesteettomyys/api/v1/accessibility/servicepoints/d26b5f28-41c6-40a3-99f9-a1b762cc8191'
//   ACCESSIBLE_MAP_URL: '${tileserverUrl}/styles/high-contrast-map-layer/{z}/{x}/{y}'
//   AIR_MONITORING_API: '${apiUrl}/environment_data/api/v1'
//   CITIES: 'turku,kaarina,naantali,raisio'
//   DIGITRANSIT_API: 'https://api.digitransit.fi/routing/v1/routers/waltti/index/graphql'
//   DIGITRANSIT_API_KEY: digitransitApiKey
//   EVENTS_API: 'https://linkedevents-api.turku.fi/v1'
//   FEEDBACK_ADDITIONAL_INFO_LINK: 'https://opaskartta.turku.fi/eFeedback/fi/Home/AboutService'
//   FEEDBACK_ADDITIONAL_INFO_LINK_EN: 'https://opaskartta.turku.fi/eFeedback/en/Home/AboutService'
//   FEEDBACK_ADDITIONAL_INFO_LINK_SV: 'https://opaskartta.turku.fi/eFeedback/sv/Home/AboutService'
//   FEEDBACK_IS_PUBLISHED: 'false'
//   FEEDBACK_URL: 'https://kehityspalvelukartta-api.turku.fi/open311/'
//   INITIAL_MAP_POSITION: '60.451799,22.266414'
//   LANG: 'en_US.utf8'
//   LC_ALL: 'en_US.UTF-8'
//   LC_LANG: 'en_US.UTF-8'
//   MAPS: 'servicemap,accessible_map'
//   MATOMO_SITE_ID: '7'
//   MATOMO_URL: 'https://matomo.turku.fi'
//   MOBILITY_PLATFORM_API: apiUrl
//   MOBILITY_TEST_API: 'https://liikkumistesti-api.turku.fi/api/v1/postalcoderesult'
//   MODE: 'production'
//   NODE_ENV: 'production'
//   OLD_MAP_LINK_EN: 'https://servicemap.turku.fi/'
//   OLD_MAP_LINK_FI: 'https://palvelukartta.turku.fi/'
//   OLD_MAP_LINK_SV: 'https://servicekarta.turku.fi/'
//   PARKING_SPACES_URL: 'https://parkkiopas.turku.fi/public/v1/parking_area/'
//   PARKING_STATISTICS_URL: 'https://parkkiopas.turku.fi/public/v1/parking_area_statistics/'
//   PORT: '2048'
//   PORTNET_API: 'https://meri.digitraffic.fi/api/port-call/v1'
//   PRODUCTION_PREFIX: 'SM'
//   RAILWAYS_API: 'https://rata.digitraffic.fi/api/v1'
//   REITTIOPAS_URL: 'https://reittiopas.foli.fi/reitti/'
//   RESERVATIONS_API: 'https://respa.turku.fi/v1'
//   ROADWORKS_API: '${apiUrl}/exceptional_situations/api/v1'
//   SERVICE_MAP_URL: '${tileserverUrl}/styles/hel-osm-bright/{z}/{x}/{y}'
//   SERVICEMAP_API: '${apiUrl}/api'
//   SERVICEMAP_API_VERSION: '/v2'
//   SHOW_AREA_SELECTION: 'true'
//   SHOW_READ_SPEAKER_BUTTON: 'false'
//   SSR_FETCH_TIMEOUT: '2500'
//   THEME_PKG: '1'
//   USE_PTV_ACCESSIBILITY_API: 'true'
//   WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'false'
// }

param apiAppSettings object = {
  ACCESSIBILITY_SYSTEM_ID: 'd26b5f28-41c6-40a3-99f9-a1b762cc8191'
  ADDITIONAL_INSTALLED_APPS: 'smbackend_turku,ptv'
  ALLOWED_HOSTS: '${apiInternalUrl},169.254.129.6,127.0.0.1,localhost,xieite.haltu.net,tkuapp228,palvelukartta-api.turku.fi,palvelukartta.turku.fi' // TODO
  APPLY_MIGRATIONS: 'true'
  CSRF_TRUSTED_ORIGINS: apiUrl
  BICYCLE_NETWORK_LOG_LEVEL: 'INFO'
  COOKIE_PREFIX: 'smdev' // TODO
  DEBUG: 'False'
  DEFAULT_FROM_EMAIL: 'palvelukartta@turku.fi' // TODO
  DJANGO_LOG_LEVEL: 'INFO'
  // DJANGO_SUPERUSER_EMAIL: 'admin@admin.com' // TODO
  // DJANGO_SUPERUSER_PASSWORD: djangoSuperuserPassword // TODO
  // DJANGO_SUPERUSER_USERNAME: 'admin' // TODO
  ECO_COUNTER_LOG_LEVEL: 'INFO'
  ECO_COUNTER_OBSERVATIONS_URL: 'https://data.turku.fi/cjtv3brqr7gectdv7rfttc/counters-15min.csv'
  ECO_COUNTER_STATIONS_URL: 'https://dev.turku.fi/datasets/ecocounter/liikennelaskimet.geojson'
  EMAIL_BACKEND: 'django.core.mail.backends.smtp.EmailBackend' // TODO
  EMAIL_FROM: 'palvelukartta@turku.fi'
  EMAIL_HOST: 'smtp.turku.fi'
  // ?EMAIL_HOST_PASSWORD: emailHostPassword // TODO
  // ?EMAIL_HOST_USER: 'apikey' // TODO
  EMAIL_PORT: '25'
  EMAIL_USE_TLS: 'True'
  ENABLE_SSH: 'true'
  ENVIRONMENT_DATA_LOG_LEVEL: 'INFO'
  EXCEPTIONAL_SITUATIONS_LOG_LEVEL: 'INFO'
  FILE_UPLOAD_PERMISSIONS: '0o644'
  GEO_SEARCH_API_KEY: geoSearchApiKey
  GEO_SEARCH_LOCATION: 'https://paikkatietohaku.api.hel.fi/v1/address/'
  INTERNAL_IPS: '127.0.0.1'
  IOT_LOG_LEVEL: 'INFO'
  KUNTEC_KEY: kuntecKey
  LAM_COUNTER_API_BASE_URL: 'https://tie.digitraffic.fi/api/tms/v1/history'
  LAM_COUNTER_STATIONS_URL: 'https://tie.digitraffic.fi/api/tms/v1/stations?lastUpdated=false&state=ACTIVE'
  LANGUAGES: 'fi,sv,en'
  MEDIA_ROOT: '/fileshare/mediaroot'
  MEDIA_URL: '/media/'
  MOBILITY_DATA_CHARGING_STATIONS_URL: 'https://services1.arcgis.com/rhs5fjYxdOG1Et61/ArcGIS/rest/services/GasFillingStations/FeatureServer/0/query?f=json&where=1%3D1&outFields=OPERATOR%2CLAT%2CLON%2CSTATION_NAME%2CADDRESS%2CCITY%2CZIP_CODE%2CLNG_CNG%2CObjectId'
  MOBILITY_DATA_GAS_FILLING_STATIONS_URL: 'https://services1.arcgis.com/rhs5fjYxdOG1Et61/ArcGIS/rest/services/ChargingStations/FeatureServer/0/query?f=json&where=1%20%3D%201%20OR%201%20%3D%201&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outFields=LOCATION_ID%2CNAME%2CADDRESS%2CURL%2COBJECTID%2CTYPE'
  MOBILITY_DATA_GEOMETRY_URL: 'https://tie.digitraffic.fi/api/v3/data/traffic-messages/area-geometries?id=11&lastUpdated=false'
  MOBILITY_DATA_LOG_LEVEL: 'INFO'
  OPEN311_API_KEY: open311ApiKey
  OPEN311_INTERNAL_API_KEY: open311InternalApiKey
  OPEN311_SERVICE_CODE: open311ServiceCode
  OPEN311_URL_BASE: 'https://opaskartta.turku.fi/efeedback/api/georeport/6aika/requests.json'
  PTV_ID_OFFSET: '10000000'
  SCM_DO_BUILD_DURING_DEPLOYMENT: '1'
  SEARCH_LOG_LEVEL: 'INFO'
  SECRET_KEY: secretKey
  SECURE_PROXY_SSL_HEADER: 'HTTP_X_FORWARDED_PROTO,https'
  SECURE_SSL_REDIRECT: 'False'
  SERVER_EMAIL: 'palvelukartta@turku.fi'
  STATIC_ROOT: '/fileshare/staticroot'
  STATIC_URL: '/static/'
  STREET_MAINTENANCE_LOG_LEVEL: 'INFO'
  TELRAAM_TOKEN: telraamToken
  TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL: 'https://data.turku.fi/2yxpk2imqi2mzxpa6e6knq/'
  TURKU_API_KEY: turkuApiKey
  TURKU_SERVICES_IMPORT_LOG_LEVEL: 'INFO'
  TURKU_WFS_URL: 'https://opaskartta.turku.fi/TeklaOGCWeb/WFS.ashx'
  USE_X_FORWARDED_HOST: 'True'
  WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'false'
  WEBSITES_PORT: '8000'
  YIT_CLIENT_ID: '01797d9f-1ab5-4d01-880d-01dfa4925a27'
  YIT_CLIENT_SECRET: yitClientSecret
  YIT_CONTRACTS_URL: 'https://api.autori.io/api/dailymaintenance-a3/contracts/'
  YIT_EVENTS_URL: 'https://api.autori.io/api/dailymaintenance-a3/route/types/operation/'
  YIT_ROUTES_URL: 'https://api.autori.io/api/dailymaintenance-a3/route/'
  YIT_SCOPE: 'api://7f45c30e-cc67-4a93-85f1-0149b44c1cdf/.default'
  YIT_TOKEN_URL: 'https://login.microsoftonline.com/86792d09-0d81-4899-8d66-95dfc96c8014/oauth2/v2.0/token?Scope=api://7f45c30e-cc67-4a93-85f1-0149b44c1cdf/.default'
  YIT_VEHICLES_URL: 'https://api.autori.io/api/dailymaintenance-a3/route/types/vehicle/'
}
// Test
// param apiAppSettings object = {
//   ACCESSIBILITY_SYSTEM_ID: 'd26b5f28-41c6-40a3-99f9-a1b762cc8191'
//   ADDITIONAL_INSTALLED_APPS: 'smbackend_turku,ptv'
//   ALLOWED_HOSTS: '${apiInternalUrl},127.0.0.1,localhost,partheite.haltu.net,tkuapp226,kehityspalvelukartta-api.turku.fi,kehityspalvelukartta.turku.fi' // TODO
//   APPLY_MIGRATIONS: 'true'
//   CSRF_TRUSTED_ORIGINS: apiUrl
//   BICYCLE_NETWORK_LOG_LEVEL: 'INFO'
//   COOKIE_PREFIX: 'smdev' // TODO
//   DEBUG: 'False'
//   DEFAULT_FROM_EMAIL: 'kehityspalvelukartta@turku.fi' // TODO
//   DJANGO_LOG_LEVEL: 'INFO'
//   DJANGO_SUPERUSER_EMAIL: 'admin@admin.com' // TODO
//   DJANGO_SUPERUSER_PASSWORD: djangoSuperuserPassword // TODO
//   DJANGO_SUPERUSER_USERNAME: 'admin' // TODO
//   ECO_COUNTER_LOG_LEVEL: 'INFO'
//   ECO_COUNTER_OBSERVATIONS_URL: 'https://data.turku.fi/cjtv3brqr7gectdv7rfttc/counters-15min.csv'
//   ECO_COUNTER_STATIONS_URL: 'https://dev.turku.fi/datasets/ecocounter/liikennelaskimet.geojson'
//   EMAIL_BACKEND: 'django.core.mail.backends.smtp.EmailBackend' // TODO
//   EMAIL_FROM: 'iikka.merilainen@rebase.fi' // TODO
//   EMAIL_HOST: 'smtp.sendgrid.net' // TODO
//   EMAIL_HOST_PASSWORD: emailHostPassword // TODO
//   EMAIL_HOST_USER: 'apikey' // TODO
//   EMAIL_PORT: '587'
//   EMAIL_USE_TLS: 'True'
//   ENABLE_SSH: 'true'
//   ENVIRONMENT_DATA_LOG_LEVEL: 'INFO'
//   EXCEPTIONAL_SITUATIONS_LOG_LEVEL: 'INFO'
//   FILE_UPLOAD_PERMISSIONS: '0o644'
//   GEO_SEARCH_API_KEY: geoSearchApiKey
//   GEO_SEARCH_LOCATION: 'https://paikkatietohaku.api.hel.fi/v1/address/'
//   INTERNAL_IPS: '127.0.0.1'
//   IOT_LOG_LEVEL: 'INFO'
//   KUNTEC_KEY: kuntecKey
//   LAM_COUNTER_API_BASE_URL: 'https://tie.digitraffic.fi/api/tms/v1/history'
//   LAM_COUNTER_STATIONS_URL: 'https://tie.digitraffic.fi/api/tms/v1/stations?lastUpdated=false'
//   LANGUAGES: 'fi,sv,en'
//   MEDIA_ROOT: '/fileshare/mediaroot'
//   MEDIA_URL: '/media/'
//   MOBILITY_DATA_CHARGING_STATIONS_URL: 'https://services1.arcgis.com/rhs5fjYxdOG1Et61/ArcGIS/rest/services/GasFillingStations/FeatureServer/0/query?f=json&where=1%3D1&outFields=OPERATOR%2CLAT%2CLON%2CSTATION_NAME%2CADDRESS%2CCITY%2CZIP_CODE%2CLNG_CNG%2CObjectId'
//   MOBILITY_DATA_GAS_FILLING_STATIONS_URL: 'https://services1.arcgis.com/rhs5fjYxdOG1Et61/ArcGIS/rest/services/ChargingStations/FeatureServer/0/query?f=json&where=1%20%3D%201%20OR%201%20%3D%201&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outFields=LOCATION_ID%2CNAME%2CADDRESS%2CURL%2COBJECTID%2CTYPE'
//   MOBILITY_DATA_GEOMETRY_URL: 'https://tie.digitraffic.fi/api/v3/data/traffic-messages/area-geometries?id=11&lastUpdated=false'
//   MOBILITY_DATA_LOG_LEVEL: 'INFO'
//   OPEN311_API_KEY: open311ApiKey
//   OPEN311_INTERNAL_API_KEY: open311InternalApiKey
//   OPEN311_SERVICE_CODE: open311ServiceCode
//   OPEN311_URL_BASE: 'https://opaskartta.turku.fi/efeedback/api/georeport/6aika/requests.json'
//   PTV_ID_OFFSET: '10000000'
//   SCM_DO_BUILD_DURING_DEPLOYMENT: '1'
//   SEARCH_LOG_LEVEL: 'INFO'
//   SECRET_KEY: secretKey
//   SECURE_PROXY_SSL_HEADER: 'HTTP_X_FORWARDED_PROTO,https'
//   SECURE_SSL_REDIRECT: 'False'
//   SERVER_EMAIL: 'kehityspalvelukartta@turku.fi'
//   STATIC_ROOT: '/fileshare/staticroot'
//   STATIC_URL: '/static/'
//   STREET_MAINTENANCE_LOG_LEVEL: 'INFO'
//   TELRAAM_TOKEN: telraamToken
//   TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL: 'https://data.turku.fi/2yxpk2imqi2mzxpa6e6knq/'
//   TURKU_API_KEY: turkuApiKey
//   TURKU_SERVICES_IMPORT_LOG_LEVEL: 'INFO'
//   TURKU_WFS_URL: 'https://opaskartta.turku.fi/TeklaOGCWeb/WFS.ashx'
//   WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'false'
//   WEBSITES_PORT: '8000'
//   YIT_CLIENT_ID: '01797d9f-1ab5-4d01-880d-01dfa4925a27'
//   YIT_CLIENT_SECRET: yitClientSecret
//   YIT_CONTRACTS_URL: 'https://api.autori.io/api/dailymaintenance-a3/contracts/'
//   YIT_EVENTS_URL: 'https://api.autori.io/api/dailymaintenance-a3/route/types/operation/'
//   YIT_ROUTES_URL: 'https://api.autori.io/api/dailymaintenance-a3/route/'
//   YIT_SCOPE: 'api://7f45c30e-cc67-4a93-85f1-0149b44c1cdf/.default'
//   YIT_TOKEN_URL: 'https://login.microsoftonline.com/86792d09-0d81-4899-8d66-95dfc96c8014/oauth2/v2.0/token?Scope=api://7f45c30e-cc67-4a93-85f1-0149b44c1cdf/.default'
//   YIT_VEHICLES_URL: 'https://api.autori.io/api/dailymaintenance-a3/route/types/vehicle/'
// }

@allowed([
  0
  1
  2
  3
  4
  5
])
param cacheCapacity int = 1

var webAppRequirements = [
  {
    name: apiWebAppName
    image: apiImageName
    allowKeyvaultSecrets: true
    applicationGatewayAccessOnly: true
    appSettings: {
      DATABASE_URL: '@Microsoft.KeyVault(VaultName=${keyvault.name};SecretName=${keyvault::dbUrlSecret.name})'
      CACHE_LOCATION: '@Microsoft.KeyVault(VaultName=${keyvault.name};SecretName=${keyvault::cacheLocationSecret.name})'
      CELERY_BROKER_URL: '@Microsoft.KeyVault(VaultName=${keyvault.name};SecretName=${keyvault::celeryBrokerUrlSecret.name})'
      ...apiAppSettings
    }
    fileshares: {
      'api-files': '/fileshare'
      'api-data': '/smbackend/data'
    }
  }
  {
    name: tileserverWebAppName
    image: tileserverImageName
    allowKeyvaultSecrets: false
    applicationGatewayAccessOnly: true
    appSettings: {}
    fileshares: {
      'tileserver-data': '/data'
    }
  }
  {
    name: uiWebAppName
    image: uiImageName
    allowKeyvaultSecrets: false
    applicationGatewayAccessOnly: true
    appSettings: uiAppSettings
    fileshares: {}
  }
]

var fileshareNames = union(flatten(map(webAppRequirements, x => objectKeys(x.fileshares))), []) // union removes duplicate keys

var dnsZoneRequirements = [
  'privatelink.azurecr.io'
  'privatelink.file.core.windows.net'
  'privatelink.postgres.database.azure.com'
  'privatelink.redis.cache.windows.net'
  'privatelink.vaultcore.azure.net'
]

var subnetRequirements = [
  {
    name: 'default'
    delegations: []
    serviceEndpoints: []
    enableNatGateway: false
  }
  {
    name: 'azureservices'
    delegations: []
    serviceEndpoints: []
    enableNatGateway: false
  }
  {
    name: 'api'
    delegations: ['Microsoft.Web/serverfarms'] // Required
    serviceEndpoints: []
    enableNatGateway: true
  }
]

var privateEndpointRequirements = [
  {
    name: '${cacheName}-endpoint'
    privateLinkServiceId: cache.id
    groupId: 'redisCache'
    privateDnsZoneName: 'privatelink.redis.cache.windows.net'
    privateDnsZoneId: dnsZone[3].id
  }
  {
    name: '${containerRegistryName}-endpoint'
    privateLinkServiceId: containerRegistry.id
    groupId: 'registry'
    privateDnsZoneName: 'privatelink.azurecr.io'
    privateDnsZoneId: dnsZone[0].id
  }
  {
    name: '${storageAccountName}-endpoint'
    privateLinkServiceId: storageAccount.id
    groupId: 'file'
    privateDnsZoneName: 'privatelink.file.core.windows.net'
    privateDnsZoneId: dnsZone[1].id
  }
  {
    name: '${keyvaultName}-endpoint'
    privatelinkServiceId: keyvault.id
    groupId: 'vault'
    privateDnsZoneName: 'privatelink.vaultcore.azure.net'
    privateDnsZoneId: dnsZone[4].id
  }
  {
    name: '${dbServerName}-endpoint'
    privateLinkServiceId: db.id
    groupId: 'postgresqlServer'
    privateDnsZoneName: 'privatelink.postgres.database.azure.com'
    privateDnsZoneId: dnsZone[2].id
  }
]

var goforeIps = {
  goforeKamppi: '81.175.255.179' // Gofore Kamppi egress
  goforeTampere: '82.141.89.43' // Gofore Tampere egress
  goforeVpn: '80.248.248.85' // Gofore VPN egress
}
var goforeCidrs = {
  goforeKamppi: '${goforeIps.goforeKamppi}/24'
  goforeTampere: '${goforeIps.goforeTampere}/24'
  goforeVpn: '${goforeIps.goforeVpn}/24'
}
var goforeAndAzureContainerRegistryIps = union(goforeIps, {
  // Needed to build an image in the container registry, networkRuleBypassOptions: AzureServices is not enough for some reason. These IPs can probably change. Sourced from https://www.microsoft.com/en-us/download/details.aspx?id=56519
  azureRange1: '51.12.32.0/25'
  azureRange2: '51.12.32.128/26'
})
var goforeStorageNetworkAcls = {
  defaultAction: 'Deny'
  ipRules: map(items(goforeIps), ip => {
    action: 'Allow'
    value: ip.value
  })
}
var goforeContainerRegistryNetworkRuleSet = {
  defaultAction: 'Deny'
  ipRules: map(items(goforeAndAzureContainerRegistryIps), ip => {
    action: 'Allow'
    value: ip.value
  })
}
var goforeNetworkAcls = {
  bypass: 'AzureServices'
  defaultAction: 'Deny'
  ipRules: map(items(goforeIps), ip => {
    value: ip.value
  })
}

resource workspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: workspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
  }
}

resource apiOutboundIp 'Microsoft.Network/publicIPAddresses@2024-01-01' existing = {
  name: apiOutboundIpName
  scope: resourceGroup('turku-common')
}

resource natGateway 'Microsoft.Network/natGateways@2024-01-01' = {
  name: natGatewayName
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    idleTimeoutInMinutes: 4
    publicIpAddresses: [
      {
        id: apiOutboundIp.id
      }
    ]
  }
}

resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: ['10.0.0.0/16']
    }
    encryption: {
      enabled: false
      enforcement: 'AllowUnencrypted'
    }
    enableDdosProtection: false
  }

  @batchSize(1)
  resource subnets 'subnets@2023-11-01' = [
    for i in range(0, length(subnetRequirements)): {
      name: subnetRequirements[i].name
      properties: {
        addressPrefixes: ['10.0.${i}.0/24']
        natGateway: subnetRequirements[i].enableNatGateway ? { id: natGateway.id } : null
        serviceEndpoints: [
          for serviceEndpoint in subnetRequirements[i].serviceEndpoints: {
            service: serviceEndpoint
            locations: [location]
          }
        ]
        delegations: [
          for delegation in subnetRequirements[i].delegations: {
            name: 'delegation'
            properties: {
              serviceName: delegation
            }
            type: 'Microsoft.Network/virtualNetworks/subnets/delegations'
          }
        ]
        privateEndpointNetworkPolicies: 'Disabled'
        privateLinkServiceNetworkPolicies: 'Enabled'
      }
    }
  ]
}

resource dnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = [
  for dnsZoneRequirement in dnsZoneRequirements: {
    name: dnsZoneRequirement
    location: 'global'
  }
]

resource privateDnsZoneVnetLinks 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = [
  for i in range(0, length(dnsZoneRequirements)): {
    parent: dnsZone[i]
    location: 'global'
    name: 'vnetlink'
    properties: {
      registrationEnabled: false
      virtualNetwork: {
        id: vnet.id
      }
    }
  }
]

resource cache 'Microsoft.Cache/Redis@2024-04-01-preview' = {
  name: cacheName
  location: location
  properties: {
    redisVersion: '6.0'
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: cacheCapacity
    }
    enableNonSslPort: false
    publicNetworkAccess: 'Disabled'
    redisConfiguration: {
      'aad-enabled': 'true'
      'maxmemory-reserved': '30'
      'maxfragmentationmemory-reserved': '30'
      'maxmemory-delta': '30'
    }
    updateChannel: 'Stable'
    disableAccessKeyAuthentication: false
  }
  dependsOn: [
    dnsZone[3]
    vnet::subnets[1]
  ]
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Premium'
  }
  properties: {
    adminUserEnabled: true // Required to create RBAC rights
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    networkRuleSet: goforeContainerRegistryNetworkRuleSet
  }
  dependsOn: [
    dnsZone[0]
    vnet::subnets[1]
  ]

  resource webhooks 'webhooks@2023-01-01-preview' = [
    for webAppRequirement in webAppRequirements: {
      name: '${replace(webAppRequirement.name, '-', '')}webhook'
      location: location
      properties: {
        actions: ['push']
        scope: '${webAppRequirement.image}:latest'
        serviceUri: '${list(resourceId('Microsoft.Web/sites/config', webAppRequirement.name, 'publishingcredentials'), '2015-08-01').properties.scmUri}/docker/hook'
        status: 'enabled'
      }
    }
  ]
}

var dbProperties = {
  storage: {
    iops: 120
    tier: 'P4'
    storageSizeGB: 32
    autoGrow: 'Disabled'
  }
  network: {
    publicNetworkAccess: 'Enabled'
  }
  dataEncryption: {
    type: 'SystemManaged'
  }
  authConfig: {
    activeDirectoryAuth: 'Disabled'
    passwordAuth: 'Enabled'
  }
  version: '16'
  administratorLogin: dbAdminUsername
  administratorLoginPassword: dbAdminPassword
  availabilityZone: '2'
}

var dbSku = {
  // Must be above Burstable for replication
  name: 'Standard_D2ds_v5'
  tier: 'GeneralPurpose'
}

resource db 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: dbServerName
  location: location
  sku: dbSku
  properties: {
    replicationRole: 'Primary'
    createMode: 'Default'
    ...dbProperties
  }
  dependsOn: [
    dnsZone[2]
    vnet::subnets[1]
  ]

  resource dbFirewallRules 'firewallRules' = [
    for ip in items(goforeIps): {
      name: ip.key
      properties: {
        startIpAddress: ip.value
        endIpAddress: ip.value
      }
    }
  ]
}

resource dbConfigurationClientEncoding 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-12-01-preview' = {
  name: 'client_encoding'
  parent: db
  properties: {
    value: 'UTF8'
    source: 'user-override'
  }
  dependsOn: [waitForDbReady]
}

resource dbConfigurationAzureExtensions 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-12-01-preview' = {
  name: 'azure.extensions'
  parent: db
  properties: {
    value: dbPostgresExtensions
    source: 'user-override'
  }
  dependsOn: [waitForDbReady]
}

resource dbDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  name: dbName
  parent: db
  properties: {
    charset: 'UTF8'
    collation: 'fi_FI.utf8'
  }
}

resource waitForDbReady 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  kind: 'AzurePowerShell'
  name: 'waitForDbReady'
  location: location
  properties: {
    azPowerShellVersion: '3.0'
    scriptContent: 'start-sleep -Seconds 500'
    cleanupPreference: 'Always'
    retentionInterval: 'PT1H'
  }
  dependsOn: [db]
}

resource waitForDbReadyAndConfigured 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  kind: 'AzurePowerShell'
  name: 'waitForDbReadyAndConfigured'
  location: location
  properties: {
    azPowerShellVersion: '3.0'
    scriptContent: 'start-sleep -Seconds 320'
    cleanupPreference: 'Always'
    retentionInterval: 'PT1H'
  }
  dependsOn: [
    dbConfigurationClientEncoding
    dbConfigurationAzureExtensions
  ]
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2024-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    dnsEndpointType: 'Standard'
    publicNetworkAccess: 'Enabled'
    networkAcls: goforeStorageNetworkAcls
    allowSharedKeyAccess: true // Required for uploading files with Azure CLI
    largeFileSharesState: 'Enabled'
    supportsHttpsTrafficOnly: true
    accessTier: 'Hot' // Required since swedencentral doesn't support others at the time of writing, even if we don't use blob storage
  }

  resource fileServices 'fileServices@2024-01-01' = {
    name: 'default'

    resource fileshares 'shares@2024-01-01' = [
      for fileshareName in fileshareNames: {
        name: fileshareName
      }
    ]
  }
}

resource serverfarmPlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: serverfarmPlanName
  location: location
  sku: {
    name: 'P0v3'
    tier: 'Premium0V3'
    size: 'P0v3'
    family: 'Pv3'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    perSiteScaling: false
    elasticScaleEnabled: false
    maximumElasticWorkerCount: 1
    isSpot: false
    reserved: true
    isXenon: false
    hyperV: false
    targetWorkerCount: 0
    targetWorkerSizeId: 0
    zoneRedundant: false
  }
}

resource privateEndpoints 'Microsoft.Network/privateEndpoints@2023-11-01' = [
  for privateEndpointRequirement in privateEndpointRequirements: {
    name: privateEndpointRequirement.name
    location: location
    properties: {
      customNetworkInterfaceName: '${privateEndpointRequirement.name}-nic'
      subnet: {
        id: vnet::subnets[1].id
      }
      privateLinkServiceConnections: [
        {
          name: privateEndpointRequirement.name
          properties: {
            privateLinkServiceId: privateEndpointRequirement.privateLinkServiceId
            groupIds: [privateEndpointRequirement.groupId]
          }
        }
      ]
    }
  }
]

resource privateDnsZoneGroups 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = [
  for i in range(0, length(privateEndpointRequirements)): {
    parent: privateEndpoints[i]
    name: 'default'
    properties: {
      privateDnsZoneConfigs: [
        {
          name: privateEndpointRequirements[i].privateDnsZoneName
          properties: {
            privateDnsZoneId: privateEndpointRequirements[i].privateDnsZoneId
          }
        }
      ]
    }
  }
]

resource applicationGatewayVnet 'Microsoft.Network/virtualNetworks@2020-11-01' existing = {
  name: 'turku-common-vnet'
  scope: resourceGroup('turku-common')
}

resource applicationGatewaySubnet 'Microsoft.Network/virtualNetworks/subnets@2022-01-01' existing = {
  name: 'AgwSubnet'
  parent: applicationGatewayVnet
}

var ipSecurityRestrictionsForGoforeIpsOnly = [
  {
    action: 'Allow'
    tag: 'Default'
    priority: 100
    name: 'AllowGoforeKamppiInbound'
    description: 'Allow HTTP/HTTPS from Application Gateway subnet'
    ipAddress: goforeCidrs.goforeKamppi
  }
  {
    action: 'Allow'
    tag: 'Default'
    priority: 101
    name: 'AllowGoforeTampereInbound'
    description: 'Allow HTTP/HTTPS from Application Gateway subnet'
    ipAddress: goforeCidrs.goforeTampere
  }
  {
    action: 'Allow'
    tag: 'Default'
    priority: 102
    name: 'AllowGoforeVpnInbound'
    description: 'Allow HTTP/HTTPS from Application Gateway subnet'
    ipAddress: goforeCidrs.goforeVpn
  }
  {
    ipAddress: 'Any'
    action: 'Deny'
    priority: 2147483647
    name: 'Deny all'
    description: 'Deny all access'
  }
]

var ipSecurityRestrictionsForApplicationGatewayAccessOnly = [
  {
    vnetSubnetResourceId: applicationGatewaySubnet.id
    action: 'Allow'
    tag: 'Default'
    priority: 100
    name: 'AllowAppGWInbound'
    description: 'Allow HTTP/HTTPS from Application Gateway subnet'
  }
  {
    ipAddress: 'Any'
    action: 'Deny'
    priority: 2147483647
    name: 'Deny all'
    description: 'Deny all access'
  }
]

resource webApps 'Microsoft.Web/sites@2023-12-01' = [
  for webAppRequirement in webAppRequirements: {
    name: webAppRequirement.name
    location: location
    kind: 'app,linux,container'
    identity: {
      type: 'SystemAssigned'
    }
    properties: {
      serverFarmId: serverfarmPlan.id
      reserved: true
      hyperV: false
      vnetRouteAllEnabled: true
      vnetImagePullEnabled: true
      vnetContentShareEnabled: false
      clientAffinityEnabled: false
      httpsOnly: true
      redundancyMode: 'None'
      publicNetworkAccess: 'Enabled'
      virtualNetworkSubnetId: vnet::subnets[2].id
      keyVaultReferenceIdentity: 'SystemAssigned'
      siteConfig: {
        numberOfWorkers: 1
        linuxFxVersion: 'DOCKER|${containerRegistryName}.azurecr.io/${webAppRequirement.image}:latest'
        acrUseManagedIdentityCreds: true
        alwaysOn: true
        http20Enabled: false
        functionAppScaleLimit: 0
        minimumElasticInstanceCount: 1
        ipSecurityRestrictionsDefaultAction: webAppRequirement.applicationGatewayAccessOnly ? 'Deny' : 'Allow'
        ipSecurityRestrictions: webAppRequirement.applicationGatewayAccessOnly
          ? ipSecurityRestrictionsForApplicationGatewayAccessOnly
          : []
        scmIpSecurityRestrictionsDefaultAction: 'Deny'
        scmIpSecurityRestrictionsUseMain: false
        scmIpSecurityRestrictions: ipSecurityRestrictionsForGoforeIpsOnly
        azureStorageAccounts: reduce(
          items(webAppRequirement.fileshares),
          {},
          (build, fileshare) =>
            union(build, {
              '${fileshare.key}-mount': {
                type: 'AzureFiles'
                accountName: storageAccountName
                shareName: fileshare.key
                mountPath: fileshare.value
                protocol: 'Smb'
                accessKey: listKeys(
                  resourceId('Microsoft.Storage/storageAccounts', storageAccountName),
                  providers('Microsoft.Storage', 'storageAccounts').apiVersions[0]
                ).keys[0].value
              }
            })
        )
        appSettings: map(
          items({
            DOCKER_ENABLE_CI: 'true'
            APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
            ApplicationInsightsAgent_EXTENSION_VERSION: '~3'
            XDT_MicrosoftApplicationInsights_Mode: 'Recommended'
            ...webAppRequirement.appSettings
          }),
          x => {
            name: x.key
            value: x.value
          }
        )
      }
    }
  }
]

resource keyvault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyvaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enabledForDeployment: true
    enabledForDiskEncryption: true
    enabledForTemplateDeployment: true
    enableRbacAuthorization: true
    enablePurgeProtection: true
    enableSoftDelete: true
    publicNetworkAccess: 'Enabled'
    networkAcls: goforeNetworkAcls
  }

  resource dbUrlSecret 'secrets' = {
    name: 'dbUrl'
    properties: {
      value: 'postgis://${dbUsername}:${dbPassword}@${dbServerName}.postgres.database.azure.com/${dbName}'
    }
  }

  resource cacheLocationSecret 'secrets' = {
    name: 'cacheLocation'
    properties: {
      value: 'rediss://:${cache.listKeys().primaryKey}@${cacheName}.redis.cache.windows.net:6380/0'
    }
  }

  resource celeryBrokerUrlSecret 'secrets' = {
    name: 'celeryBrokerUrl'
    properties: {
      value: 'rediss://:${cache.listKeys().primaryKey}@${cacheName}.redis.cache.windows.net:6380/1'
    }
  }
}

@description('Key Vault Secret User role')
resource keyVaultSecretUserRoleDefinition 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: resourceGroup()
  name: '4633458b-17de-408a-b874-0445c86b69e6'
}

@description('Container Registry AcrPull role')
resource acrPullRoleDefinition 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: resourceGroup()
  name: '7f951dda-4ed3-4680-a7ca-43fe172d538d'
}

@description('Grant the app service identity with key vault secret user role permissions over the key vault. This allows reading secret contents')
resource webAppKeyvaultSecretUserRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for i in range(0, length(webAppRequirements)): if (webAppRequirements[i].allowKeyvaultSecrets) {
    scope: keyvault
    name: guid(resourceGroup().id, webApps[i].id, keyVaultSecretUserRoleDefinition.id)
    properties: {
      roleDefinitionId: keyVaultSecretUserRoleDefinition.id
      principalId: webApps[i].identity.principalId
      principalType: 'ServicePrincipal'
    }
  }
]

@description('Grant the app service identity with ACR pull role permissions over the container registry. This allows pulling container images')
resource webAppAcrPullRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for i in range(0, length(webAppRequirements)): {
    scope: containerRegistry
    name: guid(resourceGroup().id, webApps[i].id, acrPullRoleDefinition.id)
    properties: {
      roleDefinitionId: acrPullRoleDefinition.id
      principalId: webApps[i].identity.principalId
      principalType: 'ServicePrincipal'
    }
  }
]
