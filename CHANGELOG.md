# Changelog

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
