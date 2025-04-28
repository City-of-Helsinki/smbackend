# Changelog

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
