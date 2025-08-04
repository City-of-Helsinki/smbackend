# Changelog

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
