---
name: java-openapi
description: 基于 Spring MVC 注解、JavaDoc、DTO/VO、Bean Validation、Jackson、枚举及权限代码静态分析 Spring Boot 项目，生成 OpenAPI 3.0.3 接口文档和安全测试说明；不依赖 Swagger、springdoc-openapi 或 Knife4j，不启动应用，不修改业务代码。
metadata:
  version: 0.0.2
  author: TaoGang
---

# 1. Skill 名称

`java-openapi`

---

# 2. 目标

扫描当前 Spring Boot 项目的 Java 源代码，在**不依赖 Swagger、springdoc-openapi、Knife4j 等组件**的情况下，根据：

- Spring MVC Controller 注解
- JavaDoc
- 方法签名
- DTO / VO / Request / Response / Command / Query / Form
- Bean Validation 校验注解
- Jackson 序列化注解
- Java Enum
- Spring Security / Sa-Token 权限与认证代码

静态生成符合 **OpenAPI 3.0.3** 规范的接口文档。

本 Skill：

- 不启动应用
- 不调用 `/v3/api-docs`
- 不依赖 Swagger 相关组件
- 不要求增加任何 OpenAPI 运行时依赖
- 不修改业务逻辑
- 默认仅创建或更新 `1.docs/` 目录中的文档

最终默认输出：

```text
1.docs/
├── openapi.json
└── security-test-guide.md
```

其中：

- `openapi.json`：机器可读的完整接口文档，可用于 Apifox、Postman、Burp Suite 等工具导入。
- `security-test-guide.md`：面向安全测试人员的接口交接说明，包含接口统计、认证方式、权限机制、高风险接口、安全测试关注点、JavaDoc 完整性等。

主要用于：

- 接口文档交付
- 安全测试
- 渗透测试
- 第三方接口联调
- 项目验收
- Apifox / Postman / Burp Suite 导入

---

# 3. 强制约束

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

禁止增加或修改：

```text
Swagger
swagger-core
springdoc-openapi
Knife4j
Springfox
```

默认禁止修改：

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
Request
Response
Command
Query
Form

application.yml
application.yaml
application.properties
bootstrap.yml
bootstrap.yaml
```

除非用户明确要求修改。

默认只允许创建或更新：

```text
1.docs/
```

目录中的文档文件。

---

## 3.2 不启动项目

不得为了生成 OpenAPI：

- 启动 Spring Boot
- 访问运行中的应用
- 调用 `/v3/api-docs`
- 调用 Swagger / Knife4j 页面
- 依赖运行时扫描结果

OpenAPI 必须通过**源代码静态分析**生成。

---

## 3.3 不依赖 Swagger

项目中即使完全不存在以下组件，也必须能够完成任务：

```text
swagger
swagger-core
springdoc-openapi
knife4j
springfox
```

不得要求用户为了文档生成而增加这些依赖。

---

## 3.4 不虚构业务信息

接口业务语义的来源优先级：

```text
JavaDoc
>
代码中明确的业务注释
>
注解参数
>
方法名称
>
类名称
>
字段名称
>
代码结构推断
```

JavaDoc 是主要业务语义来源。

无法可靠确认的信息：

```text
待补充
```

禁止：

- 编造业务规则
- 编造数据权限
- 编造角色权限
- 编造请求或响应字段
- 编造错误码
- 编造测试账号
- 编造 Token 获取方式
- 编造示例业务数据

---

## 3.5 不泄露敏感信息

禁止将以下真实信息写入任何生成文档：

```text
数据库密码
Redis 密码
MQ 密码
JWT Secret
Token
Access Token
Refresh Token
AES Key
RSA Private Key
SM2 Private Key
AppSecret
AccessKey
SecretKey
Cookie
SessionId
```

即使在代码或配置中发现，也不能输出具体值。

如需要描述，只能写：

```text
检测到敏感配置，具体值已隐藏。
```

---

# 4. 扫描范围与生成流程

## 4.1 默认扫描范围

扫描当前项目中所有生产代码模块。

重点扫描：

```text
src/main/java/
```

多模块项目需要扫描所有包含 Web Controller 的模块，例如：

```text
xxx-api
xxx-service
xxx-admin
xxx-web
```

不要只扫描根模块。

---

## 4.2 默认忽略

默认忽略：

```text
src/test/
target/
build/
.generated/
generated/
out/
```

除非用户明确要求纳入。

---

## 4.3 生成流程

生成 OpenAPI 前，必须先完成全量扫描和建模。

推荐执行顺序：

```text
1. 识别全部 Controller
2. 识别全部接口 Mapping
3. 识别请求参数
4. 识别请求体
5. 识别返回类型
6. 收集 DTO / VO / Enum / 泛型类型
7. 解析 Bean Validation
8. 解析 Jackson
9. 解析认证与权限
10. 构建内部 API 模型
11. 构建 OpenAPI 3.0.3 文档
12. 生成 security-test-guide.md
13. 校验生成结果
```

不得扫描一部分代码后直接开始写最终 OpenAPI。

---

## 4.4 生成前统计

生成前至少统计：

```text
Controller 数量
接口数量
DTO / VO 数量
Enum 数量
统一响应类型
认证方式
权限框架
公开接口配置
```

---

# 5. Controller、JavaDoc 与 Mapping 解析

## 5.1 Controller 识别

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
     * 根据驾驶员ID查询驾驶员详细信息。
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

应生成：

```json
{
  "/api/drivers/{id}": {
    "get": {
      "summary": "查询驾驶员详情",
      "description": "根据驾驶员ID查询驾驶员详细信息。"
    }
  }
}
```

---

## 5.2 JavaDoc 解析

重点读取：

```text
类 JavaDoc
方法 JavaDoc
字段 JavaDoc
record component JavaDoc
@param
@return
@throws
@deprecated
```

方法 JavaDoc 规则：

```java
/**
 * 新增驾驶员
 *
 * 创建新的驾驶员档案。
 *
 * @param request 驾驶员新增参数
 * @return 新增结果
 */
```

转换为：

```text
summary: 新增驾驶员
description: 创建新的驾驶员档案。
```

其中：

- JavaDoc 第一段或第一行优先作为 `summary`
- JavaDoc 后续业务说明作为 `description`
- `@param` 用于参数说明
- `@return` 用于成功响应说明
- `@deprecated` 应映射为 `deprecated: true`

---

## 5.3 JavaDoc 完整性等级

对每个接口记录文档来源等级：

```text
A：存在有效方法 JavaDoc，且主要参数说明完整
B：JavaDoc 不完整，但可结合方法名、参数名生成基础说明
C：无有效 JavaDoc，且业务语义无法可靠确认
```

最终在 `security-test-guide.md` 中统计：

```text
A级接口：xxx
B级接口：xxx
C级接口：xxx
```

对于 C 级接口：

```text
summary: 待补充
```

或者使用不带业务推断的基础方法名说明。

---

## 5.4 Tag 生成

OpenAPI `tags` 默认根据 Controller 生成。

优先使用 Controller JavaDoc。

例如：

```java
/**
 * 驾驶员管理
 */
@RestController
public class DriverController {
}
```

生成：

```json
{
  "tags": [
    "驾驶员管理"
  ]
}
```

如果 Controller 没有 JavaDoc：

可以：

- 使用 Controller 类名
- 去掉 `Controller` 后缀作为基础名称

例如：

```text
DriverController -> Driver
```

禁止凭空创建不存在的业务模块名称。

---

## 5.5 路径合并

完整接口路径必须由：

```text
Controller @RequestMapping
+
Method Mapping
```

合并生成。

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

路径拼接时需要处理：

```text
/api/drivers
/api/drivers/
/{id}
/{id}/
空路径
"/"
```

避免出现：

```text
//api
/api//drivers
```

---

## 5.6 Mapping 参数

必须识别：

```java
@GetMapping
@GetMapping("/list")
@GetMapping(value = "/list")
@GetMapping(path = "/list")

@PostMapping
@PutMapping
@DeleteMapping
@PatchMapping

@RequestMapping(method = RequestMethod.GET)
@RequestMapping(value = "/list", method = RequestMethod.GET)
```

HTTP Method 映射：

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

解析实际 `RequestMethod`。

无法确定 HTTP Method 时：

- 输出警告
- 不得默认当作 GET

---

## 5.7 多路径 / 多 Method Mapping

必须支持：

```java
@GetMapping({"/list", "/page"})
```

以及：

```java
@RequestMapping(
    value = {"/a", "/b"},
    method = {RequestMethod.GET, RequestMethod.POST}
)
```

规则：

> 如果同一个 Controller 方法映射多个 Path 或多个 HTTP Method，应展开为多个 OpenAPI Operation。

例如：

```java
@GetMapping({"/list", "/page"})
```

应生成：

```text
GET /list
GET /page
```

不得只保留第一个路径。

---

## 5.8 OperationId

每个 Operation 必须生成稳定且唯一的 `operationId`。

默认规则：

```text
Controller名称 + "_" + 方法名称
```

例如：

```text
DriverController_getDriver
```

如果一个方法映射多个 Path 或多个 Method，需确保每个 OperationId 唯一。

可追加：

```text
Method
Path序号
稳定短标识
```

禁止生成重复 OperationId。

---

## 5.9 重复接口检查

通过：

```text
HTTP Method + 完整 Path
```

唯一识别接口。

如果发现重复：

```text
发现重复接口映射：
GET /api/users/{id}
```

必须：

- 输出警告
- 在最终报告中列出
- 不得静默覆盖

---

# 6. 请求参数与请求体解析

## 6.1 参数来源

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

同时结合：

- 参数类型
- JavaDoc `@param`
- Validation 注解
- Spring 注解中的 `name` / `value`
- `required`
- `defaultValue`

生成 OpenAPI 参数。

---

## 6.2 PathVariable

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

```json
{
  "name": "id",
  "in": "path",
  "required": true,
  "description": "驾驶员ID",
  "schema": {
    "type": "integer",
    "format": "int64"
  }
}
```

Path 参数在 OpenAPI 中必须：

```text
required = true
```

即使 Spring 注解未明确写 `required = true`。

---

## 6.3 RequestParam

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

```text
required
defaultValue
name
value
```

如果存在：

```java
@RequestParam("user_name")
String userName
```

OpenAPI 参数名称必须为：

```text
user_name
```

而不是：

```text
userName
```

---

## 6.4 RequestHeader

例如：

```java
@RequestHeader("X-App-Id") String appId
```

生成：

```text
in: header
name: X-App-Id
```

对于认证类 Header：

- 先判断是否属于统一认证机制
- 如果已抽象为 `securitySchemes`，避免重复生成不必要的认证参数
- 如果只是普通业务 Header，则按普通 Header 参数生成

---

## 6.5 CookieValue

例如：

```java
@CookieValue("SESSION") String session
```

生成：

```text
in: cookie
```

如果 Cookie 属于统一 Session 认证机制：

优先考虑抽象为 SecurityScheme。

---

## 6.6 RequestBody

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

```json
{
  "requestBody": {
    "required": true,
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/DriverCreateRequest"
        }
      }
    }
  }
}
```

如果：

```java
@RequestBody(required = false)
```

则：

```text
required: false
```

---

## 6.7 ModelAttribute

对于：

```java
@ModelAttribute UserQuery query
```

应根据 Spring MVC 实际绑定方式展开为 Query 参数。

不能简单生成：

```text
requestBody
```

---

## 6.8 Content-Type

根据 Mapping 中：

```java
consumes
produces
```

生成 Content-Type。

例如：

```java
@PostMapping(
    consumes = MediaType.APPLICATION_JSON_VALUE,
    produces = MediaType.APPLICATION_JSON_VALUE
)
```

应使用代码中明确指定的值。

如果未指定：

普通 `@RequestBody` 默认可以按：

```text
application/json
```

处理。

文件上传默认按：

```text
multipart/form-data
```

处理。

如果代码明确指定其他 MediaType，以代码为准。

---

## 6.9 文件上传

识别：

```java
MultipartFile
MultipartFile[]
List<MultipartFile>
@RequestPart
```

例如单文件：

```java
@RequestPart("file")
MultipartFile file
```

生成：

```json
{
  "type": "string",
  "format": "binary"
}
```

数组文件：

```java
MultipartFile[]
```

生成：

```json
{
  "type": "array",
  "items": {
    "type": "string",
    "format": "binary"
  }
}
```

Content-Type：

```text
multipart/form-data
```

同时在 `security-test-guide.md` 中标记为安全测试关注接口。

---

# 7. Schema、DTO、泛型与类型解析

## 7.1 Schema 分析范围

递归分析接口真实引用到的：

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
Record
Enum
泛型包装对象
父类
接口定义
```

不要求无差别扫描项目中所有 Java Bean。

优先从 Controller 的：

- 请求参数
- 请求体
- 返回类型

向下递归收集依赖类型。

---

## 7.2 Java 类型映射

基本类型：

```text
String          -> string

Integer         -> integer / int32
int             -> integer / int32
Short           -> integer / int32
short           -> integer / int32
Byte            -> integer / int32
byte            -> integer / int32

Long            -> integer / int64
long            -> integer / int64
BigInteger      -> integer

Float           -> number / float
float           -> number / float
Double          -> number / double
double          -> number / double
BigDecimal      -> number

Boolean         -> boolean
boolean         -> boolean

Character       -> string
char            -> string

LocalDate       -> string / date

LocalDateTime   -> string
OffsetDateTime  -> string / date-time
ZonedDateTime   -> string / date-time
Instant         -> string / date-time
Date            -> string

UUID            -> string / uuid

byte[]          -> string / byte
```

注意：

`LocalDateTime` 是否使用 `format: date-time`，应结合项目 Jackson 格式判断。

如果项目使用：

```java
@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
```

则优先反映项目真实序列化格式，而不是强行声明 RFC3339 `date-time`。

---

## 7.3 Collection

识别：

```java
List<T>
Set<T>
Collection<T>
Iterable<T>
ArrayList<T>
LinkedList<T>
T[]
```

生成：

```json
{
  "type": "array",
  "items": {
    "$ref": "..."
  }
}
```

基础类型数组则直接生成对应基础类型。

---

## 7.4 Map

对于：

```java
Map<String, Object>
```

生成：

```json
{
  "type": "object",
  "additionalProperties": true
}
```

对于：

```java
Map<String, String>
```

生成：

```json
{
  "type": "object",
  "additionalProperties": {
    "type": "string"
  }
}
```

对于：

```java
Map<String, UserVO>
```

生成：

```json
{
  "type": "object",
  "additionalProperties": {
    "$ref": "#/components/schemas/UserVO"
  }
}
```

---

## 7.5 DTO 字段说明

字段说明优先读取字段 JavaDoc。

例如：

```java
/**
 * 驾驶员姓名
 */
private String driverName;
```

生成：

```text
description: 驾驶员姓名
```

如果没有 JavaDoc：

可以使用字段名作为最低限度描述。

例如：

```text
driverName
```

不得自动扩展为未经代码确认的业务含义。

---

## 7.6 Lombok

必须正确分析：

```java
@Data
@Getter
@Setter
@Value
@Builder
@NoArgsConstructor
@AllArgsConstructor
```

不能因为源码没有显式 getter / setter 就忽略字段。

---

## 7.7 Java Record

必须支持 Java Record。

例如：

```java
public record UserRequest(
    @NotBlank String name,
    Integer age
) {
}
```

Record component 等价于 API Schema property。

需要读取：

- component 名称
- component 类型
- JavaDoc
- Bean Validation 注解
- Jackson 注解
- 泛型信息

不能因为没有传统字段 getter/setter 而忽略。

---

## 7.8 继承字段

DTO / VO 必须分析父类字段。

例如：

```java
public class PageQuery {

    /**
     * 页码
     */
    private Integer pageNum;

    /**
     * 每页数量
     */
    private Integer pageSize;
}

public class DriverQuery extends PageQuery {

    /**
     * 驾驶员姓名
     */
    private String name;
}
```

`DriverQuery` 最终 Schema 必须体现：

```text
pageNum
pageSize
name
```

需要处理：

```text
extends
泛型父类
抽象父类
多层继承
```

如果父类字段参与 Jackson 序列化，就必须体现在最终 Schema 中。

---

## 7.9 泛型解析

必须尽量保留真实泛型类型。

例如：

```java
Result<DriverVO>
Result<List<DriverVO>>
Result<PageResult<DriverVO>>
Map<String, DriverVO>
```

不能简单统一生成：

```json
{
  "type": "object"
}
```

并丢失内部泛型信息。

---

## 7.10 统一响应对象

识别项目真实存在的统一响应包装类型，例如：

```text
Result<T>
R<T>
Response<T>
ApiResult<T>
ResponseResult<T>
```

必须读取真实 Java 定义。

禁止假设项目响应一定是：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

如果项目实际定义不同，以实际代码为准。

---

## 7.11 分页对象

识别项目实际存在的分页对象，例如：

```text
Page<T>
PageResult<T>
IPage<T>
PageInfo<T>
```

必须分析真实字段。

例如实际返回：

```json
{
  "records": [],
  "total": 100
}
```

就按真实结构生成。

不要因为看到 `Page` 就自动假设存在：

```text
pageNum
pageSize
pages
total
records
```

---

## 7.12 Schema 去重

同一 Java 类型只能对应一个稳定的：

```text
components.schemas
```

必须处理：

```text
相同类名，不同 package
```

例如：

```text
com.demo.user.dto.UserVO
com.demo.admin.dto.UserVO
```

不得互相覆盖。

可使用稳定命名，例如：

```text
UserUserVO
AdminUserVO
```

或者其他基于 package 的稳定唯一名称。

---

## 7.13 循环引用

例如：

```text
Department
 -> children
 -> List<Department>
```

必须使用 `$ref`。

不得无限递归展开 Schema。

---

# 8. Bean Validation、Jackson 与 Enum

## 8.1 Bean Validation

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

## 8.2 Required

例如：

```java
@NotBlank
private String name;
```

应将 `name` 加入对象 Schema 的：

```json
{
  "required": [
    "name"
  ]
}
```

`@NotNull`、`@NotBlank`、`@NotEmpty` 均可表示对应字段为必填约束。

---

## 8.3 字符串长度

例如：

```java
@Size(min = 2, max = 50)
private String name;
```

生成：

```json
{
  "minLength": 2,
  "maxLength": 50
}
```

---

## 8.4 集合长度

对于：

```java
@Size(min = 1, max = 10)
private List<Long> ids;
```

应生成：

```json
{
  "minItems": 1,
  "maxItems": 10
}
```

不能错误生成 `minLength` / `maxLength`。

---

## 8.5 数值范围

例如：

```java
@Min(1)
@Max(100)
private Integer age;
```

生成：

```json
{
  "minimum": 1,
  "maximum": 100
}
```

---

## 8.6 DecimalMin / DecimalMax

例如：

```java
@DecimalMin("0.01")
@DecimalMax("999.99")
private BigDecimal amount;
```

根据 OpenAPI 3.0.3 规则生成对应：

```text
minimum
maximum
exclusiveMinimum
exclusiveMaximum
```

不得把字符串值当普通字符串 Schema。

---

## 8.7 Pattern

例如：

```java
@Pattern(regexp = "\\d{11}")
private String phone;
```

生成：

```json
{
  "pattern": "\\d{11}"
}
```

不得根据正则自行扩展不存在的业务规则。

---

## 8.8 Email

例如：

```java
@Email
private String email;
```

可生成：

```json
{
  "type": "string",
  "format": "email"
}
```

---

## 8.9 Jackson 注解

识别：

```java
@JsonProperty
@JsonIgnore
@JsonIgnoreProperties
@JsonFormat
@JsonValue
@JsonCreator
@JsonInclude
```

---

## 8.10 JsonProperty

例如：

```java
@JsonProperty("driver_name")
private String driverName;
```

OpenAPI property 名称必须为：

```text
driver_name
```

而不是：

```text
driverName
```

---

## 8.11 JsonIgnore

发现：

```java
@JsonIgnore
```

默认不生成对应 API Schema 字段。

---

## 8.12 JsonIgnoreProperties

识别：

```java
@JsonIgnoreProperties(...)
```

如果明确指定忽略字段，应在最终 API Schema 中排除对应字段。

---

## 8.13 JsonFormat

例如：

```java
@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
private LocalDateTime createTime;
```

应记录真实序列化格式。

可以生成：

```json
{
  "type": "string",
  "example": "2026-09-09 10:00:00"
}
```

该示例仅用于表达格式，不得使用真实业务数据。

---

## 8.14 JsonInclude

识别：

```java
@JsonInclude(JsonInclude.Include.NON_NULL)
```

`@JsonInclude` 通常不改变 Schema property 是否存在，但会影响运行时返回字段是否可能被省略。

可在 Schema 或字段说明中适当记录：

```text
字段为 null 时可能不返回。
```

不要因此删除该字段的 Schema 定义。

---

## 8.15 Enum

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

```json
{
  "DriverStatus": {
    "type": "string",
    "enum": [
      "NORMAL",
      "DISABLED"
    ],
    "description": "NORMAL：正常；DISABLED：停用"
  }
}
```

---

## 8.16 自定义枚举值

如果 Enum 存在：

```java
private Integer code;
private String name;
```

且存在明确序列化方式，例如：

```java
@JsonValue
```

必须以实际序列化值生成 OpenAPI。

不能简单使用 Enum constant 名称。

如果无法确定真实序列化值：

- 不得猜测
- 可以保留 Enum constant
- 在说明中标记需要确认

---

# 9. Response、状态码与特殊返回类型

## 9.1 成功响应

至少根据方法真实返回类型生成一个成功响应。

默认可以生成：

```text
200
```

但必须先检查：

- `@ResponseStatus`
- `ResponseEntity`
- 方法实际语义中能够静态确定的状态码

---

## 9.2 ResponseStatus

例如：

```java
@ResponseStatus(HttpStatus.CREATED)
@PostMapping
public UserVO create(...) {
}
```

应生成：

```text
201
```

响应状态码优先级：

```text
@ResponseStatus
>
ResponseEntity 中能够静态确认的状态
>
默认成功响应 200
```

禁止因为 HTTP Method 是 POST 就自动猜测为 201。

---

## 9.3 ResponseEntity

必须识别：

```java
ResponseEntity<T>
ResponseEntity<Void>
ResponseEntity<Resource>
```

例如：

```java
ResponseEntity<UserVO>
```

响应 Schema 应为：

```text
UserVO
```

不能把 `ResponseEntity` 本身生成成业务 Schema。

如果状态码通过源码可以静态确定：

```java
return ResponseEntity.status(HttpStatus.CREATED).body(result);
```

可以使用：

```text
201
```

如果无法可靠静态确定：

按默认成功响应处理，不要猜测复杂分支中的状态码。

---

## 9.4 HttpEntity

对于：

```java
HttpEntity<T>
```

提取内部类型 `T`。

不要把 `HttpEntity` 本身当业务 Schema。

---

## 9.5 异步返回

识别：

```java
Callable<T>
DeferredResult<T>
CompletableFuture<T>
CompletionStage<T>
```

如果可以明确提取内部泛型：

```text
T
```

OpenAPI 响应 Schema 使用内部业务类型。

---

## 9.6 Void

对于：

```java
void
Void
ResponseEntity<Void>
```

响应可以没有 Schema。

不得伪造：

```json
{}
```

作为业务响应体。

---

## 9.7 文件下载

识别：

```java
Resource
InputStreamResource
ByteArrayResource
ResponseEntity<Resource>
byte[]
```

以及结合代码判断：

```java
HttpServletResponse
```

只有在 JavaDoc、方法名、Content-Type 或代码中可以合理判断为文件下载时，才标记为文件下载。

不能仅因为出现：

```java
HttpServletResponse
```

就认定一定是文件下载。

文件下载可根据实际 produces 生成：

```json
{
  "type": "string",
  "format": "binary"
}
```

---

## 9.8 错误响应

禁止凭空创建项目未定义的：

```text
400
401
403
404
500
```

如果：

- Controller
- 全局异常处理器
- JavaDoc
- 安全配置

能够明确确定某些错误响应，可以生成。

否则只在 `security-test-guide.md` 中说明相关安全测试关注点。

---

# 10. 认证、权限与安全测试关注点

本节为 OpenAPI 的附属能力。

目标是：

> 从代码中识别认证、权限和高风险接口，为安全测试部门提供测试重点。

不得把“建议测试”写成“发现漏洞”。

---

## 10.1 权限分析

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

并体现在：

```text
security-test-guide.md
```

如果 OpenAPI 可以合理表达统一 SecurityScheme，也应写入 `openapi.json`。

---

## 10.2 认证机制

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
API Key
```

根据代码判断：

```text
JWT
Bearer Token
Session
Cookie
API Key
自定义 Header
```

如果无法确认：

```text
认证方式待补充
```

不得猜测。

---

## 10.3 SecurityScheme

只有代码能够明确识别认证方式时，才生成：

```text
components.securitySchemes
```

例如确认使用：

```text
Authorization: Bearer xxx
```

可以生成：

```json
{
  "bearerAuth": {
    "type": "http",
    "scheme": "bearer"
  }
}
```

如果不能确认 Token 是否 JWT：

禁止写：

```text
bearerFormat: JWT
```

---

## 10.4 Public API

如果代码中明确存在：

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

必须以真实安全配置为准。

---

## 10.5 安全测试关注点

静态识别以下接口并写入 `security-test-guide.md`：

### 登录 / Token / 密码

关注：

```text
认证绕过
暴力破解
用户枚举
Token 重放
Token 失效
验证码绕过
```

### 用户 / 角色 / 权限 / 管理员接口

关注：

```text
水平越权
垂直越权
IDOR
权限绕过
```

### 文件上传

关注：

```text
文件类型
MIME
扩展名
双后缀
SVG / HTML
大小限制
文件覆盖
路径处理
```

### 文件下载

关注：

```text
越权下载
路径穿越
任意文件读取
敏感文件泄露
```

### 导入 / 导出

关注：

```text
越权导入导出
敏感数据泄露
恶意文件解析
CSV / Excel 公式注入
批量数据操作
```

### URL / IP / Host / RTSP / Webhook

字段或参数名称包含：

```text
url
uri
host
hostname
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

标记：

```text
建议测试 SSRF、内网访问、地址校验绕过
```

不能直接认定存在 SSRF 漏洞。

### ID / UserId / TenantId / OrgId

字段或参数包含：

```text
id
userId
driverId
companyId
tenantId
orgId
deptId
ownerId
```

结合接口语义，标记：

```text
建议测试水平越权 / IDOR / 跨租户访问
```

不能因为存在 ID 参数就直接认定存在越权漏洞。

### SQL / 排序 / 动态条件

字段或参数包含：

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

可以结合 Service / Mapper 使用方式辅助判断。

标记：

```text
动态查询参数，建议测试 SQL 注入。
```

不得直接认定存在 SQL 注入漏洞。

### 删除 / 批量修改

关注：

```text
越权删除
批量越权
参数篡改
高风险操作缺少权限校验
```

---

## 10.6 敏感数据字段

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
identityNumber

phone
mobile

bankCard
bankAccount

address
homeAddress
email
```

安全测试说明中可标记：

```text
敏感数据接口
```

但禁止输出真实敏感数据。

如果需要格式示例，只能使用脱敏或通用值，例如：

```text
张*
138****1234
3201********1234
```

---

# 11. OpenAPI 3.0.3 生成规则

## 11.1 固定版本

默认固定生成：

```json
{
  "openapi": "3.0.3"
}
```

除非用户明确要求其他 OpenAPI 版本。

---

## 11.2 顶层结构

`1.docs/openapi.json` 至少包含：

```json
{
  "openapi": "3.0.3",
  "info": {},
  "paths": {},
  "components": {
    "schemas": {}
  }
}
```

如果没有可确认的 SecurityScheme：

不得为了结构完整而虚构：

```text
components.securitySchemes
```

---

## 11.3 Info

`info.title` 优先从项目中能够可靠确认的信息获取，例如：

```text
pom.xml artifactId
pom.xml name
Gradle project name
Spring application name
项目 README 明确名称
```

如果多个来源冲突：

优先选择最明确、最接近当前服务模块的名称。

如果无法可靠判断：

```text
title: 当前服务接口
```

或：

```text
title: 待补充
```

`info.version` 如果源码中无法可靠确定：

```text
version: "1.0.0"
```

仅表示接口文档版本，不得冒充真实系统发布版本。

---

## 11.4 Server

默认不要编造：

```text
servers
```

测试环境 URL 应写入：

```text
1.docs/security-test-guide.md
```

如果源码中只能看到：

```text
server.port
context-path
```

也不足以推断真实测试环境地址。

---

## 11.5 Path

每个接口必须至少包含：

```text
HTTP Method
summary
operationId
parameters / requestBody
responses
tags
```

能够明确获取时补充：

```text
description
deprecated
security
```

---

## 11.6 Example

默认不强制生成复杂请求和响应 Example。

如果 JavaDoc 或代码中没有明确示例：

宁可不生成，也不能编造复杂业务数据。

可以生成仅用于表达格式的基础示例，例如：

```text
日期格式
时间格式
脱敏手机号
脱敏身份证
```

禁止使用代码库中的真实账号、Token、Secret 或业务数据。

---

## 11.7 响应描述

成功响应描述优先级：

```text
@return JavaDoc
>
方法 JavaDoc
>
返回类型名称
>
基础描述
```

例如：

```java
@return 驾驶员详情
```

可以生成：

```text
description: 驾驶员详情
```

---

## 11.8 OpenAPI 校验

生成 `1.docs/openapi.json` 后必须检查：

```text
JSON 语法
openapi = 3.0.3
info
paths
HTTP Method
parameters
requestBody
responses
components.schemas
components.securitySchemes
$ref
required
type
format
enum
operationId
```

重点保证：

- JSON 可解析
- `$ref` 不存在悬空引用
- Schema 名称不冲突
- OperationId 唯一
- Path 参数均 `required: true`
- multipart 文件上传格式正确
- 基础类型与数组类型正确
- 泛型未无故丢失
- 循环引用不会导致无限展开

---

# 12. security-test-guide.md 生成规则

生成：

```text
1.docs/security-test-guide.md
```

该文件同时承担：

- 人工接口总览
- 安全测试交接
- 高风险接口清单
- JavaDoc 完整性检查

不再单独生成：

```text
api-list.md
security-api-list.md
javadoc-quality-report.md
```

---

## 12.1 推荐结构

`security-test-guide.md` 至少包含：

```text
# 接口安全测试说明

## 1. 项目信息

## 2. 接口统计

## 3. OpenAPI 文件

## 4. 认证机制

## 5. 权限机制

## 6. 公开接口

## 7. 接口总览

## 8. 安全测试重点接口

### 8.1 登录 / Token / 密码
### 8.2 用户 / 角色 / 权限
### 8.3 文件上传
### 8.4 文件下载
### 8.5 导入导出
### 8.6 URL / IP / RTSP / Webhook
### 8.7 删除和批量操作
### 8.8 敏感数据接口

## 9. JavaDoc 完整性

## 10. 重复映射与文档异常

## 11. 待项目负责人补充
```

---

## 12.2 接口统计

至少统计：

```text
Controller 数量
接口总数

GET 数量
POST 数量
PUT 数量
DELETE 数量
PATCH 数量

Schema 数量
Enum 数量

A级 JavaDoc 接口数量
B级 JavaDoc 接口数量
C级 JavaDoc 接口数量

需要认证接口数量
公开接口数量

安全测试重点接口数量
```

如果无法确认认证接口数量：

标记：

```text
待补充
```

不得凭空统计。

---

## 12.3 接口总览

在 `security-test-guide.md` 中保留简洁接口表：

| 模块 | 接口名称 | Method | URL | Request | Response | 权限 |
|---|---|---|---|---|---|---|
| 驾驶员 | 查询驾驶员 | GET | /api/drivers/{id} | id | DriverVO | driver:query |

此表用于人工快速浏览。

完整机器可读接口定义以：

```text
1.docs/openapi.json
```

为准。

---

## 12.4 安全测试重点表

推荐格式：

| 接口 | Method | 关注点 | 优先级 | 测试建议 |
|---|---|---|---|---|
| /auth/login | POST | 登录认证 | 高 | 暴力破解、用户枚举 |
| /users/{id} | GET | IDOR | 高 | 水平越权 |
| /file/upload | POST | 文件上传 | 高 | MIME、后缀、大小、覆盖 |
| /video/analyze | POST | SSRF | 高 | RTSP/URL 地址校验 |

这里的：

```text
高 / 中 / 低
```

表示：

```text
安全测试优先级
```

不是漏洞等级。

禁止写：

```text
发现高危漏洞
```

除非用户明确要求进行代码安全审计，并且已有充分代码证据。

---

## 12.5 JavaDoc 完整性

至少输出：

```text
A级接口数量
B级接口数量
C级接口数量
```

并列出主要问题，例如：

| 文件 | 方法 | 问题 |
|---|---|---|
| UserController | getUser | 缺少 @param id |
| DriverController | create | 缺少方法 JavaDoc |
| UserRequest | phone | 字段缺少 JavaDoc |

该部分不再单独生成：

```text
javadoc-quality-report.md
```

---

## 12.6 测试环境信息

无法从源码确认的内容统一写：

```text
待项目负责人补充
```

例如：

```text
测试环境地址：待项目负责人补充
API Base URL：待项目负责人补充
测试账号：待项目负责人补充
管理员账号：待项目负责人补充
普通账号A：待项目负责人补充
普通账号B：待项目负责人补充
```

不得从数据库、配置文件或代码中提取真实账号密码填入文档。

---

# 13. 最终校验与输出

## 13.1 最终文件

默认只生成：

```text
1.docs/
├── openapi.json
└── security-test-guide.md
```

不要额外生成：

```text
openapi.yaml
api-list.md
security-api-list.md
javadoc-quality-report.md
```

除非用户明确要求。

---

## 13.2 最终检查

生成结束后检查：

```text
1. 仅创建或更新 1.docs/ 下的文档
2. 未修改业务 Java 代码
3. 未增加 Swagger / springdoc / Knife4j 依赖
4. openapi.json 为合法 JSON
5. OpenAPI 版本为 3.0.3
6. 所有 $ref 有效
7. OperationId 唯一
8. Path + Method 无静默覆盖
9. Schema 无类名冲突
10. JavaDoc 缺失项已列出
11. 安全测试关注点使用“建议测试”而非“发现漏洞”
12. 文档中不存在真实 Token、Secret、密码、私钥
```

如果发现修改了业务逻辑：

必须恢复。

---

## 13.3 最终摘要

任务完成后输出类似：

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

JavaDoc：
A级：168
B级：15
C级：3

需要认证接口：171
公开接口：15

安全测试重点接口：27

已生成：

1.docs/openapi.json
1.docs/security-test-guide.md
```

同时说明：

- 重复接口映射
- 无法解析的类型
- C 级 JavaDoc 接口
- 无法确认的认证机制
- 其他需要项目负责人补充的信息

---

# 14. 默认执行指令

当用户要求：

```text
生成 OpenAPI
```

或者：

```text
生成接口安全测试文档
```

默认执行：

```text
扫描当前 Spring Boot 项目。

不得使用 Swagger、springdoc-openapi、Knife4j 等组件。

不得启动项目，也不得调用 /v3/api-docs。

不得修改任何业务 Java 代码。

根据 Spring MVC Controller 注解、JavaDoc、方法签名、
DTO、VO、Request、Response、Record、泛型、继承关系、
Bean Validation、Jackson、Enum、Spring Security 或 Sa-Token
进行静态分析。

生成符合 OpenAPI 3.0.3 规范的：

1.docs/openapi.json

同时生成：

1.docs/security-test-guide.md

接口业务描述优先使用 JavaDoc。

无法确认的信息写“待补充”。

禁止虚构业务规则、权限规则、错误码和测试账号。

禁止在文档中输出密码、Token、Secret、Private Key、
AccessKey、数据库密码等敏感信息。

security-test-guide.md 中同时包含：

- 接口统计
- 接口总览
- 认证与权限说明
- 高风险接口清单
- 安全测试关注点
- JavaDoc 完整性
- 待补充信息

生成结束后必须校验 openapi.json：

- JSON 语法正确
- OpenAPI 版本为 3.0.3
- 所有 $ref 有效
- OperationId 唯一
- Schema 无冲突
- Path 参数正确
- 请求体和响应类型正确
- 文件上传下载格式正确
- 泛型、Record、继承 DTO 正确解析
```

---

# 15. 推荐触发语句

```text
使用 java-openapi Skill，扫描当前 Spring Boot 项目。

不要修改任何业务代码，
不要增加 Swagger、springdoc-openapi 或 Knife4j 依赖，
不要启动应用。

完全根据 Controller、JavaDoc、DTO、VO、Request、Response、
Java Record、Bean Validation、Jackson、Enum、继承关系、
泛型和权限代码进行静态分析。

生成：

1.docs/openapi.json
1.docs/security-test-guide.md

OpenAPI 固定使用 3.0.3。

其中 security-test-guide.md 需要包含：

- 接口统计
- 接口总览
- 认证和权限机制
- 安全测试重点接口
- JavaDoc 完整性
- 待项目负责人补充的信息

生成结果用于提供给安全测试部门。
```
