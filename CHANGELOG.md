# Changelog

## [3.15.3](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.15.2...smbackend-v3.15.3) (2026-02-18)


### Dependencies

* Bump sqlparse from 0.5.3 to 0.5.4 ([ddf7299](https://github.com/City-of-Helsinki/smbackend/commit/ddf7299e5cc4629eeefd4c9edd30fdeedecb20eb))

## [3.15.2](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.15.1...smbackend-v3.15.2) (2026-02-13)


### Bug Fixes

* Mock geocode_address in test_address_filter ([85ad493](https://github.com/City-of-Helsinki/smbackend/commit/85ad493b80e6fa317731a79d8ddccb5f9646c24c))
* Prevent SQL injection in search queries ([11a0ae7](https://github.com/City-of-Helsinki/smbackend/commit/11a0ae7143689286750c9086f237b21bd242dca7))
* **search:** Sanitize search query operands better ([b5032c6](https://github.com/City-of-Helsinki/smbackend/commit/b5032c63ae1ef17c52e8ead2dab9b94b26a4c162))

## [3.15.1](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.15.0...smbackend-v3.15.1) (2026-02-10)


### Bug Fixes

* **services:** Eliminate n+1 query in unit detail endpoint ([6bb0d8f](https://github.com/City-of-Helsinki/smbackend/commit/6bb0d8f1c552c418444d3c0cfc97cb43b73e845f))


### Performance Improvements

* **search:** Optimize service and unit queries in API ([34fb0da](https://github.com/City-of-Helsinki/smbackend/commit/34fb0da84696ef330b53720f6e69ce0fa567e099))

## [3.15.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.14.1...smbackend-v3.15.0) (2026-02-06)


### Features

* **vantaa parking areas:** Support MultiLineString and fix pagination ([a879ec3](https://github.com/City-of-Helsinki/smbackend/commit/a879ec3667804d0049a3a6ef5cc999a082a992b4))

## [3.14.1](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.14.0...smbackend-v3.14.1) (2026-02-05)


### Dependencies

* Bump django from 5.2.9 to 5.2.11 ([06042bd](https://github.com/City-of-Helsinki/smbackend/commit/06042bd5bd6ebdc561982e9498a837377ba6eec5))
* Bump pip from 25.2 to 26.0 ([b9c43ce](https://github.com/City-of-Helsinki/smbackend/commit/b9c43cec626abeea8f128366ad2157913343a26b))

## [3.14.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.13.0...smbackend-v3.14.0) (2026-01-28)


### Features

* **services:** Add retry logic and timeout to external API calls ([3835300](https://github.com/City-of-Helsinki/smbackend/commit/383530073731cf991fe5a6309126639c56d06136))


### Performance Improvements

* Optimize unit filtering queries ([470fb17](https://github.com/City-of-Helsinki/smbackend/commit/470fb17af20325ffdc177bf46acccb9f7b8db378))


### Dependencies

* Bump wheel from 0.45.1 to 0.46.2 ([1e2d0c8](https://github.com/City-of-Helsinki/smbackend/commit/1e2d0c82d5d3da99b6c83bbf2071fe329319ae73))

## [3.13.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.12.0...smbackend-v3.13.0) (2026-01-22)


### Features

* Update indoor facility accessibility rules ([2b66175](https://github.com/City-of-Helsinki/smbackend/commit/2b661758339142f899c9228b84306db505f328d9))
* Update outdoor sports facility accessibility rules ([8eabf34](https://github.com/City-of-Helsinki/smbackend/commit/8eabf340f500f945d1f9b7581bd31171ec88c74e))


### Bug Fixes

* **accessibility:** Add null check for variable_path ([e19a39d](https://github.com/City-of-Helsinki/smbackend/commit/e19a39d29cc64ed09d2a38bee1efb4a722a5cc7e))


### Dependencies

* Bump django-munigeo ([7481db2](https://github.com/City-of-Helsinki/smbackend/commit/7481db2717d1228514154e21f190a143ffe67fc9))

## [3.12.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.11.0...smbackend-v3.12.0) (2026-01-12)


### Features

* Update accessibility rules ([f9190bf](https://github.com/City-of-Helsinki/smbackend/commit/f9190bfb1fb0948d87d76f2912e5eeb0aa309a72))
* Update sledding initial observable props ([3169af2](https://github.com/City-of-Helsinki/smbackend/commit/3169af2820dbaaaa433d5bf14debebc22c47192f))


### Bug Fixes

* Add explicit PROJECTION_SRID-setting ([303f554](https://github.com/City-of-Helsinki/smbackend/commit/303f554cdf15698a93b92351103b0ace2a77fcbb))
* Add import data path to settings ([63d4f3d](https://github.com/City-of-Helsinki/smbackend/commit/63d4f3dbf9f852ec64af3841f11b835521bf8aca))
* Include only active units to search view ([6c9f9d2](https://github.com/City-of-Helsinki/smbackend/commit/6c9f9d2b05b2d0c5836f966906b9f549e048ba7a))
* Return use of certain base image ([38edd25](https://github.com/City-of-Helsinki/smbackend/commit/38edd2574b685a5ef0337bf5e085b7f88ee423d0))
* Update sledding initial observable props ([db9fbfe](https://github.com/City-of-Helsinki/smbackend/commit/db9fbfe8ecf96d31df0b2b9ba4ca7f0078e66ae2))
* Update Vantaa stat-districts forecast import ([8a51dfc](https://github.com/City-of-Helsinki/smbackend/commit/8a51dfcb9b1bc692167ecf5156cbd7e73a0b874c))
* Use latest base image ([ab6418c](https://github.com/City-of-Helsinki/smbackend/commit/ab6418c16047d069ddd97f0a835018ee50d4a328))
* Use latest base image ([#357](https://github.com/City-of-Helsinki/smbackend/issues/357)) ([523dc5d](https://github.com/City-of-Helsinki/smbackend/commit/523dc5d53f8a3c2f0e9d0ed69035a289fa2eb9ea))


### Dependencies

* Bump django-munigeo ([9782f6d](https://github.com/City-of-Helsinki/smbackend/commit/9782f6d3f012d7f5de6d433c295ca7957fab3c65))

## [3.11.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.10.1...smbackend-v3.11.0) (2025-12-09)


### Features

* Allow Sentry uWSGI-plugin to be optional ([22694c0](https://github.com/City-of-Helsinki/smbackend/commit/22694c0c371fa25dfed6b02819a287e949c101f6))


### Bug Fixes

* Use certain base image for older gdal ([c3c3d86](https://github.com/City-of-Helsinki/smbackend/commit/c3c3d86ad2129c48633294b6141a762bd3408200))

## [3.10.1](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.10.0...smbackend-v3.10.1) (2025-12-04)


### Dependencies

* Bump django from 5.2.8 to 5.2.9 ([68eeae5](https://github.com/City-of-Helsinki/smbackend/commit/68eeae5151e6ca753751900ca416e074ad597b94))

## [3.10.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.9.1...smbackend-v3.10.0) (2025-11-12)


### Features

* Change logging format to json ([b639314](https://github.com/City-of-Helsinki/smbackend/commit/b6393143214f904192dc1a36a7b886d71fd69205))
* Configure uwsgi for json logging ([b844fed](https://github.com/City-of-Helsinki/smbackend/commit/b844fedbd71ad62b136ec6cc88ec638c221e45eb))
* Enable request id logging ([21a2da9](https://github.com/City-of-Helsinki/smbackend/commit/21a2da937689ec7f8907c6f1ba98222e1b3ff27d))
* Remove release notes script ([8379d72](https://github.com/City-of-Helsinki/smbackend/commit/8379d72727ede64f9e95445b94bc47afc61b74bf))


### Dependencies

* Bump pip-tools ([c2dabfd](https://github.com/City-of-Helsinki/smbackend/commit/c2dabfd7ace5397aee7d880bea2b6d5566710372))
* Move ipython to main requirements for improved console ([698643e](https://github.com/City-of-Helsinki/smbackend/commit/698643ee2731577df638e2ee305cf5ce71c2d86c))
* Remove ruff from dev requirements ([fd2fb8b](https://github.com/City-of-Helsinki/smbackend/commit/fd2fb8b2cc15f630382ed5a391bd863ee3095d65))

## [3.9.1](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.9.0...smbackend-v3.9.1) (2025-11-10)


### Dependencies

* Bump django from 5.2.7 to 5.2.8 ([62ff365](https://github.com/City-of-Helsinki/smbackend/commit/62ff36577c9bd21a2a6ac5ad06ca7b692d528678))
* Bump pip from 25.2 to 25.3 ([27ace72](https://github.com/City-of-Helsinki/smbackend/commit/27ace7297260cda889c3d034c6e63bb64bc0ef17))

## [3.9.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.8.2...smbackend-v3.9.0) (2025-11-03)


### Features

* Allow dynamic sentry trace ignore paths ([d66f861](https://github.com/City-of-Helsinki/smbackend/commit/d66f861995627245e9d19977a54221523235f80c))


### Bug Fixes

* Remove 'py-call-uwsgi-fork-hooks'-option ([9b09a11](https://github.com/City-of-Helsinki/smbackend/commit/9b09a11e0073f9306b6d0f4bc8a5e447c6112816))
* Update uwsgi-config for Sentry ([ee45ee1](https://github.com/City-of-Helsinki/smbackend/commit/ee45ee1cba143487b4cea9f7b2a131ce6db0b480))


### Dependencies

* Bump sentry-sdk and uwsgi versions ([0b87d52](https://github.com/City-of-Helsinki/smbackend/commit/0b87d52f44d3ec7081238f55dd5787f469563020))

## [3.8.2](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.8.1...smbackend-v3.8.2) (2025-10-15)


### Dependencies

* Bump django from 5.1.12 to 5.2.7 ([33bbc79](https://github.com/City-of-Helsinki/smbackend/commit/33bbc79888fa51ddc581ff44cc46bb3b60825097))
* Upgrade packages, add hashes ([3d93344](https://github.com/City-of-Helsinki/smbackend/commit/3d933444d733115300bcb5076ea3263e7cf7e47d))

## [3.8.1](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.8.0...smbackend-v3.8.1) (2025-10-10)


### Bug Fixes

* Add missing cors headers for sentry ([2be7dfa](https://github.com/City-of-Helsinki/smbackend/commit/2be7dfa6f5f66620dc0b831a43edd5bfe3d04d0c))

## [3.8.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.7.1...smbackend-v3.8.0) (2025-10-09)


### Features

* **sentry:** Update sentry configuration ([f2ff4b9](https://github.com/City-of-Helsinki/smbackend/commit/f2ff4b9ad2f609e668bc7d3e6f3ce513aebdf71a))


### Dependencies

* Bump django from 5.1.12 to 5.1.13 ([eb96445](https://github.com/City-of-Helsinki/smbackend/commit/eb96445107e82b23993fea728e75ca25180c3200))
* Bump sentry-sdk from 2.16.0 to 2.39.0 ([5fc83d1](https://github.com/City-of-Helsinki/smbackend/commit/5fc83d11c29db9e301aeb765ae75cffe96b60066))

## [3.7.1](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.7.0...smbackend-v3.7.1) (2025-09-10)


### Dependencies

* Bump django from 5.1.11 to 5.1.12 ([f8e9411](https://github.com/City-of-Helsinki/smbackend/commit/f8e94115eecdeee10049db4206e6b4ef5597cb0f))

## [3.7.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.6.1...smbackend-v3.7.0) (2025-08-18)


### Features

* Combine school district update commands ([351a482](https://github.com/City-of-Helsinki/smbackend/commit/351a482c381e9c805627fe9c3b4100ba1051c5d0))
* Implement django-csp ([63cca17](https://github.com/City-of-Helsinki/smbackend/commit/63cca172020e655d0a93f4c22d0da421a09c732c))
* Picture url rewrite support and endpoints ([6b0f342](https://github.com/City-of-Helsinki/smbackend/commit/6b0f342b7816043f7a199b78f75ebaf185d713f4))


### Bug Fixes

* Retain earlier district data on importer error ([2e412a2](https://github.com/City-of-Helsinki/smbackend/commit/2e412a268d458a47bd4c8e818958551281c1d87d))
* Wrap preschool import in a transaction ([17c477f](https://github.com/City-of-Helsinki/smbackend/commit/17c477f5ed550edb52e7c7245a0abe934de0e8b1))


### Performance Improvements

* Optimize observation queries ([d85b84f](https://github.com/City-of-Helsinki/smbackend/commit/d85b84fd24dd0ab5144170cd394b25513bbe13ac))


### Dependencies

* Add django-csp ([013cf9d](https://github.com/City-of-Helsinki/smbackend/commit/013cf9d89f40eb0e3e3f61297aae31d5a44b5db0))

## [3.6.1](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.6.0...smbackend-v3.6.1) (2025-08-04)


### Dependencies

* Downgrade urllib3 ([c32464c](https://github.com/City-of-Helsinki/smbackend/commit/c32464ca106adde32b83d07afae49e7725e62779))

## [3.6.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.5.2...smbackend-v3.6.0) (2025-07-21)


### Features

* Adapt to new statistical districts API ([24c5564](https://github.com/City-of-Helsinki/smbackend/commit/24c55645b8f74ec45c7936e28c4b663e64a89a15))
* **division:** Set units to empty if no units are found ([3aade0e](https://github.com/City-of-Helsinki/smbackend/commit/3aade0eeb5a142ac1ecb2c77e2ef39c84a20fb14))
* Improve uWSGI options ([9355f55](https://github.com/City-of-Helsinki/smbackend/commit/9355f55774904ef86e5a2a12cfa6356ec4f45e73))


### Dependencies

* Add uwsgitop ([6f19156](https://github.com/City-of-Helsinki/smbackend/commit/6f19156f5d8bf0024951c0570fc6b80c0846aff4))
* Bump urllib3 from 1.26.20 to 2.5.0 ([4dd0c67](https://github.com/City-of-Helsinki/smbackend/commit/4dd0c67b35459b3afa61f424131dc27360186f14))

## [3.5.2](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.5.1...smbackend-v3.5.2) (2025-06-11)


### Dependencies

* Bump django from 5.1.10 to 5.1.11 ([4e1dfae](https://github.com/City-of-Helsinki/smbackend/commit/4e1dfae6f0ed18ddeef06f5e75d0a33ba498a49a))
* Bump requests from 2.32.3 to 2.32.4 ([ba08511](https://github.com/City-of-Helsinki/smbackend/commit/ba085119d781d41e5dc82ee5d4ea60b39433f590))

## [3.5.1](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.5.0...smbackend-v3.5.1) (2025-06-10)


### Dependencies

* Bump django from 5.1.9 to 5.1.10 ([dee55b6](https://github.com/City-of-Helsinki/smbackend/commit/dee55b61b5de84a7fa8776c90df8530f074d49a0))

## [3.5.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.4.1...smbackend-v3.5.0) (2025-05-20)


### Features

* Update accessibility rules for restaurants ([9f1e6d0](https://github.com/City-of-Helsinki/smbackend/commit/9f1e6d03e527048783fd2ea8aab0e50deefb07af))

## [3.4.1](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.4.0...smbackend-v3.4.1) (2025-05-14)


### Dependencies

* Bump django from 5.1.8 to 5.1.9 ([d60d989](https://github.com/City-of-Helsinki/smbackend/commit/d60d989e7b5a5f05482478d5e747f0bd3c4b2382))

## [3.4.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.3.1...smbackend-v3.4.0) (2025-04-28)


### Features

* **observations:** Add initial observable properties for sledding ([72bfe02](https://github.com/City-of-Helsinki/smbackend/commit/72bfe02b25fdbc8a071e78bba00535889525aa71))
* **observations:** Add new allowed value for swimming conditions ([4affe41](https://github.com/City-of-Helsinki/smbackend/commit/4affe41b06d8ca722b711a08646084c367863b0a))


### Dependencies

* Bump django from 5.1.7 to 5.1.8 ([a8bb3df](https://github.com/City-of-Helsinki/smbackend/commit/a8bb3dfb9ff7d27d2713ab2836dbb7af69d643f1))

## [3.3.1](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.3.0...smbackend-v3.3.1) (2025-03-07)


### Dependencies

* Bump cryptography from 43.0.1 to 44.0.1 ([8babaa4](https://github.com/City-of-Helsinki/smbackend/commit/8babaa4106fe9e921ddd2dcf09235ba8264d9751))
* Bump django from 5.1.5 to 5.1.7 ([d007222](https://github.com/City-of-Helsinki/smbackend/commit/d007222a87596cb820f07ce4378833296f09d7d8))

## [3.3.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.2.0...smbackend-v3.3.0) (2025-02-12)


### Features

* **school:** Import school districts without units ([be5f514](https://github.com/City-of-Helsinki/smbackend/commit/be5f5142a61892ecf43b1f859b4dd17f82745169))
* **school:** Run school district import inside a transaction ([6e131a4](https://github.com/City-of-Helsinki/smbackend/commit/6e131a48a06570fc91503ca812485fcd4609127b))

## [3.2.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.1.0...smbackend-v3.2.0) (2025-02-11)


### Features

* Switch to City of Helsinki's UBI GDAL image ([f17857f](https://github.com/City-of-Helsinki/smbackend/commit/f17857f902aa2ecdd13a0bd10d8e78fd2f6effb0))


### Bug Fixes

* Remove default value for secret key ([58aba58](https://github.com/City-of-Helsinki/smbackend/commit/58aba5874d3712a5b6b2a65a0ebb78358da24aa2))

## [3.1.0](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.0.1...smbackend-v3.1.0) (2025-02-05)


### Features

* Use database password if present in env ([#284](https://github.com/City-of-Helsinki/smbackend/issues/284)) ([3eb710e](https://github.com/City-of-Helsinki/smbackend/commit/3eb710ef9d19fa33ec0d4e95adefa07ea7dfb05d))


### Bug Fixes

* **import:** Skip broken divisions in school district import ([bbb9cc3](https://github.com/City-of-Helsinki/smbackend/commit/bbb9cc37f5f7ee1762327cd54569c24abf471cdb))

## [3.0.1](https://github.com/City-of-Helsinki/smbackend/compare/smbackend-v3.0.0...smbackend-v3.0.1) (2025-01-29)


### Bug Fixes

* **search:** Rework search query building ([b3e70c4](https://github.com/City-of-Helsinki/smbackend/commit/b3e70c40d87d9b83d34b50c1755826ff1f88a00b))


### Dependencies

* Split dev requirements from requirements.in ([b957191](https://github.com/City-of-Helsinki/smbackend/commit/b95719164bc91385660fd6fd4df8c92942e0901c))
