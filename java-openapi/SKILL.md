---
name: java-openapi
description: 将SpringBoot 项目中接口生成OpenAPI 文件时使用。
metadata:
  version: 0.0.0
  author: TaoGang
---

## 1. Skill 名称

`java-openapi`

---

# 2. 目标

扫描当前 Spring Boot 项目的 Java 源代码，在**不依赖 Swagger、springdoc-openapi、Knife4j 等组件**的情况下，根据：

- Spring MVC Controller 注解
- JavaDoc
- 方法签名
- DTO / VO / Request / Response
- Bean Validation 参数校验注解
- 枚举
- Spring Security / Sa-Token 权限信息

静态生成符合 **OpenAPI 3.x** 规范的接口文档。

本 Skill 不启动应用，不调用 `/v3/api-docs`，不要求项目增加任何 Swagger 相关依赖。

最终输出：

```text
docs/
├── openapi.yaml
├── openapi.json
├── api-list.md
├── security-api-list.md
└── security-test-guide.md
```

主要用于：

- 接口文档交付
- 安全测试
- 渗透测试
- 第三方接口联调
- 项目验收
- Apifox / Postman / Burp Suite 导入

---

# 3. 核心原则

## 3.1 零侵入

禁止为了生成文档修改业务代码。

禁止增加：

```java
@Operation
@Parameter
@Schema
@ApiResponse
@ApiResponses
@Tag
@SecurityRequirement
```

禁止增加 Swagger 或 springdoc 依赖。

禁止修改：

```text
pom.xml
build.gradle

Controller
Service
Mapper
Repository
Entity
DTO
VO

application.yml
application.properties
```

除非用户明确要求修改。

默认只允许创建或更新：

```text
1.docs/
```

目录中的文档文件。

---

# 4. 不依赖 Swagger

项目中即使完全不存在以下组件，也必须能够生成 OpenAPI：

```text
swagger
swagger-core
springdoc-openapi
knife4j
springfox
```

OpenAPI 文件通过**源代码静态分析**生成。

不得要求项目启动。

不得通过：

```text
/v3/api-docs
/swagger-resources
```

获取接口信息。

---

# 5. 信息来源优先级

接口描述信息严格按照以下优先级获取：

```text
JavaDoc
>
代码中明确的注释
>
方法名称
>
类名称
>
字段名称
>
代码结构推断
```

JavaDoc 是主要的业务语义来源。

不能明确判断的信息不得虚构。

统一标记：

```text
待补充
```

---

# 6. Controller 扫描

扫描：

```java
@RestController
@Controller
```

识别类级路径：

```java
@RequestMapping
```

识别方法级路径：

```java
@GetMapping
@PostMapping
@PutMapping
@DeleteMapping
@PatchMapping
@RequestMapping
```

例如：

```java
/**
 * 驾驶员管理
 */
@RestController
@RequestMapping("/api/drivers")
public class DriverController {

    /**
     * 查询驾驶员详情
     *
     * @param id 驾驶员ID
     * @return 驾驶员详情
     */
    @GetMapping("/{id}")
    public Result<DriverVO> get(@PathVariable Long id) {
        ...
    }
}
```

生成：

```yaml
/api/drivers/{id}:
  get:
    summary: 查询驾驶员详情
```

---

# 7. JavaDoc 解析

重点读取：

```text
类 JavaDoc
方法 JavaDoc
字段 JavaDoc
@param
@return
@throws
@deprecated
```

例如：

```java
/**
 * 新增驾驶员
 *
 * 创建新的驾驶员档案。
 *
 * @param request 驾驶员新增参数
 * @return 新增结果
 */
@PostMapping
public Result<Long> create(@RequestBody DriverCreateRequest request) {
}
```

应解析为：

```yaml
summary: 新增驾驶员
description: 创建新的驾驶员档案。
```

---

# 8. 接口名称生成

接口 `summary` 优先取 JavaDoc 第一行。

例如：

```java
/**
 * 查询驾驶员详情
 *
 * 根据驾驶员ID查询驾驶员详细信息。
 */
```

生成：

```yaml
summary: 查询驾驶员详情
description: 根据驾驶员ID查询驾驶员详细信息。
```

如果没有 JavaDoc：

可以根据方法名辅助判断。

例如：

```text
getDriver
queryDriver
listDriver
createDriver
updateDriver
deleteDriver
```

但不得虚构具体业务规则。

例如不能因为：

```java
getDriver()
```

就擅自生成：

```text
查询当前企业所属驾驶员
```

除非代码或 JavaDoc 明确体现。

---

# 9. Tag 生成

OpenAPI `tags` 默认根据 Controller 生成。

优先取 Controller JavaDoc。

例如：

```java
/**
 * 驾驶员管理
 */
@RestController
public class DriverController
```

生成：

```yaml
tags:
  - 驾驶员管理
```

没有 JavaDoc 时：

```text
DriverController
```

可以转换为：

```text
Driver
```

或者保留类名。

禁止凭空创建不存在的业务模块。

---

# 10. 请求路径解析

必须合并：

```text
Controller @RequestMapping
+
Method Mapping
```

例如：

```java
@RequestMapping("/api/drivers")
```

和：

```java
@GetMapping("/{id}")
```

生成：

```text
/api/drivers/{id}
```

同时正确识别：

```java
@GetMapping
@GetMapping("/")
@GetMapping("/list")
@GetMapping(value = "/list")
@GetMapping(path = "/list")
@RequestMapping(method = RequestMethod.GET)
```

---

# 11. HTTP Method

映射：

```text
@GetMapping      -> GET
@PostMapping     -> POST
@PutMapping      -> PUT
@DeleteMapping   -> DELETE
@PatchMapping    -> PATCH
```

对于：

```java
@RequestMapping(method = RequestMethod.POST)
```

解析实际 RequestMethod。

无法确定 HTTP Method 时：

标记警告，不得默认设置为 GET。

---

# 12. 参数来源

识别：

```java
@PathVariable
@RequestParam
@RequestHeader
@RequestBody
@RequestPart
@CookieValue
@ModelAttribute
```

生成对应 OpenAPI 参数。

---

# 13. PathVariable

例如：

```java
/**
 * @param id 驾驶员ID
 */
@GetMapping("/{id}")
public Result<DriverVO> get(
        @PathVariable Long id) {
}
```

生成：

```yaml
parameters:
  - name: id
    in: path
    required: true
    description: 驾驶员ID
    schema:
      type: integer
      format: int64
```

Path 参数必须：

```text
required: true
```

---

# 14. RequestParam

例如：

```java
/**
 * @param keyword 关键字
 * @param pageNum 页码
 */
@GetMapping
public Result<?> list(
        @RequestParam(required = false) String keyword,
        @RequestParam(defaultValue = "1") Integer pageNum) {
}
```

生成 Query 参数。

必须识别：

```java
required
defaultValue
name
value
```

---

# 15. RequestHeader

例如：

```java
@RequestHeader("X-App-Id") String appId
```

生成：

```yaml
in: header
```

认证类 Header 需要额外判断是否应该生成 `securitySchemes`。

---

# 16. RequestBody

识别：

```java
@RequestBody
```

例如：

```java
@PostMapping
public Result<Long> create(
        @RequestBody DriverCreateRequest request) {
}
```

生成：

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        $ref: '#/components/schemas/DriverCreateRequest'
```

如果：

```java
@RequestBody(required = false)
```

则：

```yaml
required: false
```

---

# 17. DTO / VO 分析

递归分析：

```text
Request
DTO
VO
Response
Command
Query
Form
Entity
POJO
```

根据 Java 字段生成：

```yaml
components:
  schemas:
```

例如：

```java
public class DriverCreateRequest {

    /**
     * 姓名
     */
    private String name;

    /**
     * 身份证号码
     */
    private String idCard;
}
```

生成：

```yaml
DriverCreateRequest:
  type: object
  properties:
    name:
      type: string
      description: 姓名
    idCard:
      type: string
      description: 身份证号码
```

---

# 18. DTO 字段说明

字段描述优先读取字段 JavaDoc。

例如：

```java
/**
 * 驾驶员姓名
 */
private String driverName;
```

生成：

```yaml
description: 驾驶员姓名
```

如果没有 JavaDoc：

可以使用字段名称作为基础描述。

例如：

```text
driverName
```

不得猜测额外业务含义。

---

# 19. Lombok

必须正确分析使用 Lombok 的对象：

```java
@Data
@Getter
@Setter
@Value
@Builder
@NoArgsConstructor
@AllArgsConstructor
```

不能因为源码没有 getter/setter 就忽略字段。

---

# 20. Java 类型映射

基本类型转换：

```text
String          -> string

Integer         -> integer / int32
int             -> integer / int32

Long            -> integer / int64
long            -> integer / int64

Float           -> number / float
Double          -> number / double
BigDecimal      -> number

Boolean         -> boolean

LocalDate       -> string / date

LocalDateTime   -> string / date-time
OffsetDateTime  -> string / date-time
Instant         -> string / date-time

UUID            -> string / uuid

byte[]          -> string / byte
```

---

# 21. Collection

识别：

```java
List<T>
Set<T>
Collection<T>
ArrayList<T>
T[]
```

生成：

```yaml
type: array
items:
  $ref: ...
```

例如：

```java
List<DriverVO>
```

生成：

```yaml
type: array
items:
  $ref: '#/components/schemas/DriverVO'
```

---

# 22. Map

对于：

```java
Map<String, Object>
```

生成：

```yaml
type: object
additionalProperties: true
```

对于：

```java
Map<String, String>
```

生成：

```yaml
type: object
additionalProperties:
  type: string
```

---

# 23. Bean Validation

识别：

```java
@NotNull
@NotBlank
@NotEmpty

@Size
@Length

@Min
@Max

@DecimalMin
@DecimalMax

@Positive
@PositiveOrZero
@Negative
@NegativeOrZero

@Pattern
@Email

@Past
@PastOrPresent
@Future
@FutureOrPresent

@Valid
@Validated
```

---

# 24. Required

例如：

```java
@NotBlank
private String name;
```

则 `name` 必须加入 Schema：

```yaml
required:
  - name
```

---

# 25. 字符串长度

例如：

```java
@Size(min = 2, max = 50)
private String name;
```

生成：

```yaml
minLength: 2
maxLength: 50
```

---

# 26. 数值范围

例如：

```java
@Min(1)
@Max(100)
private Integer age;
```

生成：

```yaml
minimum: 1
maximum: 100
```

---

# 27. Pattern

例如：

```java
@Pattern(regexp = "\\d{11}")
private String phone;
```

可以生成：

```yaml
pattern: '\d{11}'
```

但不得把正则转换成自己猜测的业务规则。

---

# 28. Enum

识别 Java Enum。

例如：

```java
/**
 * 驾驶员状态
 */
public enum DriverStatus {

    /**
     * 正常
     */
    NORMAL,

    /**
     * 停用
     */
    DISABLED
}
```

生成：

```yaml
DriverStatus:
  type: string
  enum:
    - NORMAL
    - DISABLED
```

description 中可以补充：

```text
NORMAL：正常
DISABLED：停用
```

---

# 29. 自定义枚举值

如果 Enum 使用：

```java
private Integer code;
private String name;
```

并且存在明确的 JSON 序列化方式，例如：

```java
@JsonValue
```

应以实际序列化值生成 OpenAPI。

不能简单使用 Enum constant 名称。

---

# 30. Jackson 分析

识别：

```java
@JsonProperty
@JsonIgnore
@JsonIgnoreProperties
@JsonFormat
@JsonValue
@JsonCreator
```

例如：

```java
@JsonProperty("driver_name")
private String driverName;
```

OpenAPI 字段名称应为：

```text
driver_name
```

不是：

```text
driverName
```

---

# 31. 忽略字段

发现：

```java
@JsonIgnore
```

默认不生成对应 API Schema 字段。

---

# 32. 时间格式

例如：

```java
@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
private LocalDateTime createTime;
```

Schema 中可增加：

```yaml
example: "2026-09-09 10:00:00"
```

但不得生成真实业务数据。

---

# 33. 分页对象

如果项目存在统一分页对象，例如：

```text
Page<T>
PageResult<T>
IPage<T>
PageInfo<T>
```

分析实际字段。

不要默认假设分页结构。

例如项目真正返回：

```json
{
  "records": [],
  "total": 100
}
```

就按照实际 Java 类型生成。

---

# 34. 统一响应对象

识别：

```text
Result<T>
R<T>
Response<T>
ApiResult<T>
ResponseResult<T>
```

递归读取实际定义。

禁止假设项目统一响应一定是：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

必须按照实际 Java 类生成。

---

# 35. 泛型解析

必须解析：

```java
Result<DriverVO>
Result<List<DriverVO>>
Result<PageResult<DriverVO>>
```

尽量生成准确的 OpenAPI Schema。

不能简单生成：

```yaml
type: object
```

并丢失内部泛型类型。

---

# 36. 文件上传

识别：

```java
MultipartFile
MultipartFile[]
List<MultipartFile>
@RequestPart
```

Content-Type：

```text
multipart/form-data
```

生成：

```yaml
type: string
format: binary
```

同时加入安全风险识别。

---

# 37. 文件下载

识别以下返回值：

```java
Resource
InputStreamResource
ByteArrayResource
byte[]
ResponseEntity<Resource>
```

以及直接写：

```java
HttpServletResponse
```

结合方法 JavaDoc、方法名和代码判断是否属于文件下载。

不能仅因为出现：

```java
HttpServletResponse
```

就直接认定一定是文件下载。

---

# 38. Content-Type

根据：

```java
consumes
produces
```

生成 OpenAPI。

例如：

```java
@PostMapping(
    consumes = MediaType.APPLICATION_JSON_VALUE,
    produces = MediaType.APPLICATION_JSON_VALUE
)
```

没有配置时：

普通 `@RequestBody` 默认可按：

```text
application/json
```

处理。

文件上传默认：

```text
multipart/form-data
```

---

# 39. 权限分析

扫描：

```java
@PreAuthorize
@PostAuthorize
@Secured
@RolesAllowed
```

以及 Sa-Token：

```java
@SaCheckLogin
@SaCheckRole
@SaCheckPermission
```

例如：

```java
@PreAuthorize("hasAuthority('driver:query')")
```

记录：

```text
driver:query
```

并写入：

```text
api-list.md
security-api-list.md
```

---

# 40. 认证机制

扫描项目中的：

```text
SecurityFilterChain
OncePerRequestFilter
JWT
Bearer
Authorization
Token
Sa-Token
Session
Cookie
```

根据代码判断：

```text
JWT
Bearer Token
Session
Cookie
API Key
```

如果无法确认：

标记：

```text
认证方式待补充
```

不得猜测。

---

# 41. SecurityScheme

只有当代码能够明确识别认证方式时，才生成 OpenAPI：

```yaml
components:
  securitySchemes:
```

例如确认使用：

```text
Authorization: Bearer xxx
```

可以生成：

```yaml
bearerAuth:
  type: http
  scheme: bearer
```

如果不能确认 Token 是否 JWT：

不要写：

```yaml
bearerFormat: JWT
```

---

# 42. Public API

如果代码中明确配置：

```text
permitAll
anonymous
excludePathPatterns
```

则识别公开接口。

例如：

```text
/login
/captcha
```

但需要以实际安全配置为准。

---

# 43. 高风险接口分析

除 OpenAPI 外，需要为安全测试部门自动识别高风险接口。

重点识别：

- 登录认证
- 密码修改
- Token
- 用户管理
- 角色管理
- 权限管理
- 文件上传
- 文件下载
- 数据导入
- 数据导出
- URL 参数
- IP 参数
- 回调地址
- RTSP 地址
- Webhook
- 动态查询条件
- SQL
- 删除
- 批量删除
- 批量修改
- 敏感数据查询
- 管理员接口

---

# 44. SSRF 风险

参数或字段包含：

```text
url
uri
host
ip
domain
endpoint
callback
callbackUrl
redirectUrl
webhook
streamUrl
rtspUrl
```

标记可能存在：

```text
SSRF
内网访问
地址绕过
```

但只能标记为：

```text
建议测试
```

不能直接判断代码存在漏洞。

---

# 45. 越权风险

如果接口存在：

```text
userId
driverId
companyId
tenantId
orgId
deptId
ownerId
```

以及各种：

```text
/{id}
```

需要标记：

```text
建议测试水平越权 / IDOR
```

如果存在管理员接口：

标记：

```text
建议测试垂直越权
```

不能因为存在 ID 参数就直接认定存在越权漏洞。

---

# 46. SQL 注入关注点

参数名称包含：

```text
sql
where
condition
orderBy
sort
column
field
filter
```

需要结合 Mapper / Service 使用方式辅助判断。

如果只是：

```java
String sort
```

不能直接判定存在 SQL 注入。

只标记：

```text
动态查询参数，建议测试 SQL 注入。
```

---

# 47. 敏感字段

识别：

```text
password
passwd
secret
token
accessToken
refreshToken
appSecret

idCard
identityCard

phone
mobile

bankCard
bankAccount

address
email
```

文档中禁止输出真实敏感数据。

示例必须脱敏：

```text
张*
138****1234
3201********1234
```

---

# 48. 不读取真实 Secret

禁止将以下内容写入任何文档：

```text
数据库密码
Redis 密码
MQ 密码
JWT Secret
Token
AES Key
RSA Private Key
SM2 Private Key
AppSecret
AccessKey
SecretKey
```

即使在源代码或配置文件中发现，也不能输出。

---

# 49. openapi.yaml

生成：

```text
docs/openapi.yaml
```

必须符合：

```text
OpenAPI 3.x
```

至少包含：

```yaml
openapi:
info:
paths:
components:
```

---

# 50. openapi.json

同时根据同一 OpenAPI 数据模型生成：

```text
docs/openapi.json
```

JSON 和 YAML 内容必须保持一致。

禁止分别分析后独立生成，避免结果不一致。

---

# 51. API List

生成：

```text
docs/api-list.md
```

格式：

| 模块 | 接口名称 | Method | URL | Request | Response | 权限 |
|---|---|---|---|---|---|---|
| 驾驶员 | 查询驾驶员 | GET | /api/drivers/{id} | id | DriverVO | driver:query |

---

# 52. Security API List

生成：

```text
docs/security-api-list.md
```

格式：

| 接口 | Method | 风险关注点 | 风险等级 | 测试建议 |
|---|---|---|---|---|
| /auth/login | POST | 登录认证 | 高 | 暴力破解、用户枚举 |
| /users/{id} | GET | IDOR | 高 | 水平越权 |
| /file/upload | POST | 文件上传 | 高 | 类型、大小、后缀绕过 |
| /video/analyze | POST | SSRF | 高 | RTSP/URL 地址校验 |

这里的风险等级表示：

```text
安全测试优先级
```

不是漏洞等级。

不得写成：

```text
发现高危漏洞
```

除非用户明确要求进行漏洞代码审计并确实发现问题。

---

# 53. Security Test Guide

生成：

```text
docs/security-test-guide.md
```

至少包含：

```text
项目名称

接口总数

API Base Path

认证机制

权限机制

公开接口

管理接口

文件上传接口

文件下载接口

导入导出接口

URL / IP / RTSP 参数接口

敏感数据接口

高风险操作接口

安全测试重点

待项目负责人补充事项
```

---

# 54. 测试环境信息

无法从源码确认的信息统一写：

```text
待项目负责人补充
```

例如：

```text
测试环境地址：待项目负责人补充
测试账号：待项目负责人补充
管理员账号：待项目负责人补充
普通账号A：待项目负责人补充
普通账号B：待项目负责人补充
```

---

# 55. JavaDoc 缺失处理

如果某接口没有 JavaDoc：

仍然生成 OpenAPI。

但是：

```yaml
summary:
```

可以根据方法名生成最基础描述。

同时在最终报告中统计：

```text
JavaDoc 完整接口：120
JavaDoc 缺失接口：16
```

建议列出缺失 JavaDoc 的接口。

---

# 56. JavaDoc 质量检查

同时检查：

- Controller 是否存在说明
- 接口是否存在 JavaDoc
- `@param` 是否完整
- `@return` 是否存在
- DTO 字段是否有 JavaDoc
- JavaDoc 参数名是否与实际参数匹配

生成：

```text
docs/javadoc-quality-report.md
```

可包含：

| 文件 | 方法 | 问题 |
|---|---|---|
| UserController | getUser | 缺少 @param id |
| DriverController | create | 缺少方法 JavaDoc |
| UserRequest | phone | 字段缺少 JavaDoc |

---

# 57. 多模块项目

如果是 Maven / Gradle 多模块项目：

扫描所有包含 Web Controller 的模块。

例如：

```text
xxx-api
xxx-service
xxx-admin
xxx-web
```

不要只扫描根模块。

---

# 58. 忽略测试 Controller

默认忽略：

```text
src/test/
target/
build/
.generated/
```

除非用户明确要求纳入测试接口。

---

# 59. 内部接口

如果代码或包结构明确表示：

```text
internal
inner
private-api
```

仍可以生成 OpenAPI，但在 `api-list.md` 中标记：

```text
内部接口
```

---

# 60. 生成前检查

开始生成前先完成：

```text
Controller 数量
接口数量
DTO 数量
Enum 数量
统一响应类型
认证方式
权限框架
```

不得边扫描一部分代码边直接生成最终 OpenAPI。

---

# 61. Schema 去重

同一 Java 类型只能对应一个：

```text
components.schemas
```

需要处理：

```text
相同类名不同 package
```

例如：

```text
com.demo.user.dto.UserVO
com.demo.admin.dto.UserVO
```

发生冲突时，可生成：

```text
UserUserVO
AdminUserVO
```

或其他稳定唯一名称。

不得互相覆盖。

---

# 62. 循环引用

例如：

```text
Department
 -> children
 -> List<Department>
```

使用 `$ref`。

避免无限递归生成 Schema。

---

# 63. 接口去重

通过：

```text
HTTP Method + 完整 Path
```

唯一识别接口。

如果发现重复：

输出警告：

```text
发现重复接口映射：
GET /api/users/{id}
```

不得默默覆盖。

---

# 64. OpenAPI 校验

生成后检查：

- YAML 语法
- JSON 语法
- OpenAPI version
- paths
- parameters
- requestBody
- responses
- components.schemas
- `$ref`
- required
- type
- format
- enum
- operationId

确保 `$ref` 不存在悬空引用。

---

# 65. OperationId

建议使用：

```text
Controller名称 + 方法名称
```

例如：

```text
DriverController_getDriver
```

确保唯一。

---

# 66. Response

至少根据方法真实返回类型生成：

```yaml
responses:
  '200':
```

不能凭空创建项目未定义的：

```text
400
401
403
404
500
```

如果安全框架能够明确确定：

可以补充认证相关响应说明。

否则只在安全测试指南中进行说明。

---

# 67. 不虚构 Example

默认不强制生成请求和响应 Example。

如果 JavaDoc 或代码中没有明确示例：

宁可不生成 example，也不能编造复杂业务数据。

如果需要基础类型示例：

可以生成无敏感性的通用值。

---

# 68. 最终输出

任务完成后给出：

```text
OpenAPI 静态生成完成。

Controller：32
接口：186

GET：80
POST：63
PUT：21
DELETE：18
PATCH：4

Schema：96
Enum：17

JavaDoc 完整接口：168
JavaDoc 缺失接口：18

需要认证接口：171
公开接口：15

安全测试重点接口：27

已生成：

docs/openapi.yaml
docs/openapi.json
docs/api-list.md
docs/security-api-list.md
docs/security-test-guide.md
docs/javadoc-quality-report.md
```

同时说明发现的主要文档问题。

---

# 69. 默认执行指令

当用户要求：

```text
生成 OpenAPI
```

默认执行：

```text
扫描当前 Spring Boot 项目。

不得使用 Swagger、springdoc-openapi、Knife4j 等组件。

不得启动项目获取 /v3/api-docs。

不得修改任何业务 Java 代码。

根据 Spring MVC 注解、JavaDoc、方法签名、DTO、VO、
Bean Validation、Jackson、Enum、Spring Security 或 Sa-Token
进行静态分析。

生成符合 OpenAPI 3.x 规范的：

docs/openapi.yaml
docs/openapi.json

并同时生成：

docs/api-list.md
docs/security-api-list.md
docs/security-test-guide.md
docs/javadoc-quality-report.md

接口业务描述优先使用 JavaDoc。

无法确认的信息写“待补充”。

禁止虚构业务规则。

禁止在文档中输出密码、Token、Secret、Private Key、
AccessKey、数据库密码等敏感信息。

生成结束后校验 OpenAPI 文件，
确保所有 $ref、Schema、Path、Parameter 均有效。
```

---

# 70. 推荐触发语句

```text
使用 springboot-javadoc-openapi-generator Skill，
扫描当前 Spring Boot 项目。

不要修改任何业务代码，
不要增加 Swagger 或 springdoc 依赖。

完全根据 Controller、JavaDoc、DTO、VO、
Bean Validation、Jackson 和权限代码进行静态分析。

生成：

docs/openapi.yaml
docs/openapi.json
docs/api-list.md
docs/security-api-list.md
docs/security-test-guide.md
docs/javadoc-quality-report.md

生成的 OpenAPI 用于提供给安全测试部门。
```
