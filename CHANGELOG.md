<!--next-version-placeholder-->

## v1.7.0 (2023-03-16)
### Feature
* Made list prompt parsing more accurate using yaml's loader ([`548bc01`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/548bc017751ceeee6c1eb686eebcca35f330109a))

## v1.6.0 (2023-03-16)
### Feature
* Changed the name of variable types in the project configuration to use names that represent the intent better ([`07f6c64`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/07f6c648435b0b34a4f25d08c31ffdb0739470cc))

## v1.5.0 (2023-03-14)
### Feature
* Added a switch to enable/disable the cache ([`7517277`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/751727775ac2c5ee4e202315762b3f7f1b31ec43))

## v1.4.0 (2023-03-10)
### Feature
* Added support for toml settings ([`2ad67d4`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/2ad67d497aefa501465e0518a23134157b3987e5))

### Fix
* Fixed a bug preventing users from using '~' to specify the home path from the environment variable ([`3a11bac`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/3a11baced69c46dcc15955badc614a8bd47543d5))

## v1.3.2 (2023-03-09)
### Fix
* Added a project settings class to include inside the project instead of the global settings class to better manage which options are included in the project settings ([`edc9c59`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/edc9c5967ceb03c403b8d1ca9ac5073c783632d7))
* Fixed an issue that prevented the recursive merge strategy from being applied properly ([`a0cf057`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/a0cf0573f4b83759eb252dee2c5aeb62cc1cc7d0))

## v1.3.1 (2023-03-09)
### Fix
* We are now excluding variables from project rendering because they are not part of the end product ([`ffd2a58`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/ffd2a58365a41c923a8ddc919b077bea568c6cdc))

## v1.3.0 (2023-03-09)
### Feature
* Added support for github cli as a dependency type ([`81e5379`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/81e5379de9cc94cbfe480b6571f13a561eb7551a))

### Fix
* Changed HTTP to http in git url constants ([`f7ab47e`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/f7ab47ef081d323ba6b41cbeb634ccf96ea317e2))
* Removed autoescape because it kept adding invalid characters ([`c3a8e26`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/c3a8e26f2380790f72eb4f7519739a17de5cde49))

## v1.2.0 (2023-03-08)
### Feature
* Reworked templating to make it recursive ([`41a6833`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/41a683308ac4a561a07f158254afeb9f29cc4b04))

## v1.1.0 (2023-03-05)
### Feature
* Added a CachedRepository class to handle cached git repositories (automatic updates, more versatile version options, etc.) ([`8549a48`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/8549a483b61b8daa0d0cc93c229064cee3d6c8b2))

## v1.0.0 (2023-03-02)
### Feature
* Added a clear command to the cli ([`d937df2`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/d937df28bf6c0fc48d5ee75d2981aa6e108df9a2))

### Breaking
* adding a second command to the CLI means it will not pick 'create' as the default command and must be explicitly used  ([`d937df2`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/d937df28bf6c0fc48d5ee75d2981aa6e108df9a2))

## v0.6.0 (2023-02-16)
### Feature
* Added settings override levels (default, global, project) ([`07c01e0`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/07c01e0a259139486348d5254aeb688b3f43b74a))

## v0.5.0 (2023-02-14)
### Feature
* BREAKING CHANGE (build trigger) ([`adfa4d8`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/adfa4d88dffa61e9529890cbebfdf0030429c588))
* BREAKING CHANGE, (rebuild) ([`1996039`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/1996039211846ddd1720c30ffab68a1354b8764b))

## v0.4.2 (2023-02-14)
### Fix
* Binaries get copied now instead of raising a UnicodeDecodeError ([`4b30be5`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/4b30be5da76e856208b31baad1aeb2b538802f0b))

## v0.4.1 (2023-02-14)
### Fix
* Allowed to use values or names in name based enums ([`0f8b334`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/0f8b3348246e25532828241add1944c24a5145c0))

## v0.4.0 (2023-02-13)
### Feature
* Added logging in cli ([`6da3ca7`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/6da3ca733bfa62b5771bc4e19de9d71c10b2cb8e))

## v0.3.0 (2023-02-06)
### Feature
* Added a 'variables' property in the Context class for ease of use ([`a6e8160`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/a6e81600da49fe1c347ad2c3123ac16e5bc0e060))

### Documentation
* Fixed typo in docstring ([`529b52b`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/529b52b539a476f7fcff9fa90c53c8d17da9b97a))
* Updated docstrings (better formatting) ([`08ce939`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/08ce939b73c2982b12016b55a2bd4915024d6e46))

## v0.2.0 (2023-01-25)
### Feature
* Added non interactive mode ([`dc6ce22`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/dc6ce225c5315c13bf7ddd66ea7ab31aee6d8b5e))

## v0.1.0 (2022-12-22)
### Feature
* Project ready for publishing ([`62423e6`](https://github.com/alexisbeaulieu97/SuperTemplater/commit/62423e6bb2547417b3d44827c75fd3a7c183d2b2))