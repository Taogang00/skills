---
name: java-dev
description: 为 Guanwei Java/Spring Boot 后端项目提供代码编写、重构和审查规范。项目使用 guanwei-* Starter、com.guanwei 包名，或用户明确要求遵循本规范时使用。普通 Java 教学、非 Guanwei 项目及其他技术栈不应套用公司专属约定。
metadata:
  version: 1.0.4
  author: TaoGang
---

# Java 开发代码规范

本规范整合 Java 通用实践与 Guanwei 公司约定，适用于能够通过 `guanwei-*` Starter、`com.guanwei` 包名或用户说明识别出的 Guanwei Java 后端项目。

执行规则时，按以下顺序判断：

1. 用户对当前任务的明确要求。
2. 当前项目的 `pom.xml`、父级 BOM、已有代码结构和同模块惯例。
3. 本规范中的公司约定。

开始编写或修改代码前，先检查项目实际技术栈和相邻实现。项目现状与本文版本示例不一致时，以项目实际配置为准，并向用户说明有实质影响的差异。

---

## 一、技术栈
### 1.1 常用技术栈（新项目默认值，已有项目以实际 `pom.xml` 和父级 BOM 为准）
- Java 17+
- Maven 3.6+
- Spring Boot 3.5+
- MyBatisPlus 3.5.16， 数据库的ORM
- MyBatisPlusJoin 1.5.7， 多表关联查询，对MyBatisPlus联表查询增强框架，文档：https://mybatis-plus-join.github.io/pages/quickstart/quickstart.html
- FastJson2， 用于springboot接口消息转换
- MapStruct，DTO、VO、Entity 对象转换框架

### 1.2 公司自定义封装的springboot starter 说明
- guanwei-boot-starter-toi 封装了针对运政业务的feign调用，方便各个业务模块进行调用。
- guanwei-boot-starter-workflow 封装了开发者公司工作流的使用。
- guanwei-boot-starter-mybatis 针对MyBatisPlus进行数据库操作，提供基础的增删改查、sql执行打印、分页插件封装、分页结果封装。
- guanwei-boot-starter-json 针对Fastjson封装，支持json转换、数据脱敏`@Sensitive`、数据加密`@BootEncResult`、枚举字段序列化转义`@EnumDescribe`。
- guanwei-boot-starter-token-core 提供jwt、jws、jwe、rsa非对称加密的token生成、token解析、token校验功能，接口token鉴权使用`@BootToken`，接口不需要token鉴权使用`@BootNonToken`。
- guanwei-boot-starter-token 提供`guanwei-boot-starter-token-core` 与`spring-boot-starter-web`进行整合，对接口进行token校验。
- guanwei-boot-starter-diff 提供对象的比对功能。
- guanwei-boot-starter-err 全局统一异常处理。
- guanwei-boot-starter-feign  提供feign远程调用与guanwei-boot 框架的整合。
- guanwei-boot-starter-s3  提供s3与guanwei-boot 框架的整合。
- guanwei-boot-starter-s3-web  提供s3与`spring-boot-starter-web` 框架的整合。
- guanwei-boot-starter-xxljob  提供xxljob与guanwei-boot 框架的整合。
- guanwei-boot-starter-sse 提供sse与guanwei-boot 框架的整合。

## 二、一级军规

- 所有项目依赖版本必须统一由父级BOM进行管理，禁止子模块自行指定版本，禁止多版本依赖混用
- 所有的类名保持统一风格的名称前缀，如系统管理模块，所有的类名都以Sys开头，如SysUser、SysUserController、SysUserService、SysUserServiceImpl、SysUserViewDTO、SysUserMapStruct、SysUserPageQuery
- 所有的类名必须见名知意，简单的、随意的命名禁止使用， 如`EnumState、UserInfo、DataDTO、CommonDTO`（过于宽泛），`EnumUserState、SysUserDetailDTO、OrderPageQuery`（体现模块+职责）
- 仅当文件包含明确的代码生成标记、项目文档说明其由生成器维护，或用户明确确认时，才将其视为不可直接修改的生成文件。需要扩展时使用项目已有的扩展点或新增业务侧扩展类；无法判断是否为生成文件时，先检查生成配置或询问用户。
- 所有Controller层只进行参数接收，参数校验，调用service，返回结果。禁止复杂的业务数据的处理，业务处理必须在service层进行
- 所有Controller层禁止直接调用数据库Mapper接口进行数据库操作，如果有需要重构改造，将业务处理放到service层。
- 所有Controller层使用统一的返回体类`com.guanwei.core.utils.result.R<T>`，`T`必须填写明确的业务数据类型；无响应数据时使用`R<Void>`，禁止使用`R<?>`。
- 所有Controller层中只能使用`GET`和`POST` 两种请求方式，不允许使用`PUT`、`DELETE`、`PATCH`、`OPTIONS`、`HEAD`、`TRACE`等。
- 所有Controller层方法参数禁止使用`Map<String, Object>`、`JSONObject`、`JsonNode`、`ObjectNode`等弱类型对象作为请求参数接收体，必须使用DTO请求体对象。请求体对象必须添加必要的校验注解，并使用`@Validated`触发参数校验。
- 所有Controller层方法返回的数据类型必须明确，禁止使用`Object`、`Map<String, Object>`等弱类型。
- 所有Controller层分页接口，接口的参数必须继承`com.guanwei.core.utils.page.PageQuery`，类名使用类似XxxPageQuery，体现分页的职能。
- 所有Controller层禁止直接返回数据库Entity对象，Controller层必须使用DTO对象作为返回体。
- 除Controller层和Feign接口外，其他方法禁止使用`com.guanwei.core.utils.result.R<T>`作为返回体，应直接返回明确的领域类型。
- 所有的分页查询对象必须继承`com.guanwei.core.utils.page.PageQuery`，类名使用类似XxxPageQuery，体现该类分页的职能。
- 简单的单表，联表查询使用MybatisPlus+MybatisPlusJoin 实现即可，不需要自定义Mapper接口和写xml映射文件，减少冗余代码。
- 对于单表操作，Service接口继承`com.guanwei.mybatis.base.service.MBaseService<Entity>`；对应实现类继承`com.guanwei.mybatis.base.service.MBaseServiceImpl<Mapper, Entity>`并实现该Service接口。
- 对于单表操作，Mapper接口继承`com.guanwei.mybatis.base.mapper.MBaseMapper<Entity>`。
- 项目中只需要定义DTO类，禁止定义VO、BO等其他对象；接口请求使用`XxxFormDTO`，响应使用`XxxViewDTO`，具体约束见下文“FormDTO 与 ViewDTO 约束”。
- 禁止使用`BeanUtils.copyProperties`等反射式工具复制对象属性，具体约束见下文“FormDTO 与 ViewDTO 约束”。
- 当一段代码具有独立业务语义、需要隔离复杂度或便于单元测试时，可以提取为私有方法；不要仅为减少行数而机械拆分。

### 2.1 FormDTO 与 ViewDTO 约束

- `XxxFormDTO`：仅用于Controller层接收前端提交的请求体数据，表示表单输入对象。所有POST请求中需要通过`@RequestBody`接收的业务请求对象，必须使用`XxxFormDTO`命名。
- `XxxViewDTO`：仅用于Controller层向前端返回业务展示数据，表示前端查看、展示所需的数据对象。所有Controller层返回的业务数据必须使用`XxxViewDTO`或其集合、分页结构作为数据类型，禁止直接返回Entity。
- `XxxFormDTO`主要描述“前端提交什么数据”，字段以接口实际需要接收的数据为准，不要求与数据库Entity字段完全一致；禁止为了与Entity保持一致而无意义地复制全部字段。
- `XxxViewDTO`主要描述“前端需要看到什么数据”，字段以接口实际展示需求为准，不要求与数据库Entity字段完全一致；禁止直接将Entity作为`XxxViewDTO`的替代品。
- `XxxFormDTO`与`XxxViewDTO`职责必须严格分离，禁止为了复用字段而将同一个DTO同时作为请求参数和响应结果使用。
- `XxxViewDTO`可以根据前端不同展示场景进行扩展，例如`XxxSimpleViewDTO`、`XxxDetailViewDTO`、`XxxExViewDTO`，但必须保持以`ViewDTO`结尾。
- `XxxFormDTO`中的字段必须根据业务及参数要求添加必要的校验注解，并配合Controller层的`@Validated`进行参数校验。
- 创建和修改场景，如果请求字段、校验规则或业务语义存在明显差异，应分别定义`XxxCreateFormDTO`和`XxxUpdateFormDTO`，禁止为了减少DTO数量而强行复用同一个FormDTO。
- 查询条件不属于表单提交对象，查询接口优先使用`XxxQuery`或分页场景使用`XxxPageQuery`，不要为了统一命名而全部使用`XxxFormDTO`。
- DTO之间禁止通过继承关系强行复用业务字段来规避对象定义；只有在字段和业务语义确实存在明确的“基础对象+扩展对象”关系时，才允许使用继承。
- Entity、FormDTO、ViewDTO之间的对象转换统一使用MapStruct完成，禁止使用`BeanUtils.copyProperties`等反射式属性复制工具。


### 2.2 统一接口响应结构
```java
@SuppressWarnings("unused")
@Data
public class R<T> implements Serializable {

    /**
     * 结果是否加密
     */
    private int isEncrypt;

    /**
     * 成功标识
     */
    private boolean success;

    /**
     * 响应消息
     */
    private String msg;

    /**
     * 响应详情
     */
    private String detail;

    /**
     * 返回数据
     */
    private T data;

    public R() {
    }

    public R(boolean success, String msg, T data) {
        this.success = success;
        this.msg = msg;
        this.data = data;
    }

    public R(boolean success, String msg, String detail, T data) {
        this.success = success;
        this.msg = msg;
        this.detail = detail;
        this.data = data;
    }

    public R(String msg, T data) {
        this.msg = msg;
        this.data = data;
    }

    public R(T data) {
        this.data = data;
    }

    public static <T> R<T> OK() {
        return new R<>(true, "请求成功", null);
    }

    public static <T> R<T> OK(String msg, T data) {
        return new R<>(true, msg, data);
    }

    public static <T> R<T> OK(T data) {
        return new R<>(true, "请求成功", data);
    }

    public static <T> R<T> ERROR() {
        return new R<>(false, "请求失败", null);
    }

    public static <T> R<T> ERROR(String msg, T data) {
        return new R<>(false, msg, data);
    }

    public static <T> R<T> ERROR(String msg, String detail, T data) {
        return new R<>(false, msg, detail, data);
    }

    public static <T> R<T> ERROR(String msg) {
        return new R<>(false, msg, null);
    }

    public static <T> R<T> ERROR(T data) {
        return new R<>("请求失败", data);
    }
}

```

### 2.3 Controller层示例方法
```java
// Controller只负责参数接收、校验、调用Service和封装响应
@GetMapping("/list")
public R<List<AiProfileTagViewDTO>> list(@Validated AiProfileTagPageQuery query) {
    return R.OK(aiProfileTagService.listPage(query));
}

// 新增一条记录，必须使用POST方法，必须添加@Validated注解
@PostMapping
public R<Boolean> add(@Validated @RequestBody AiProfileTagCreateFormDTO dto) {
    return R.OK(aiProfileTagService.add(dto));
}

// 更新一条记录，使用POST方法，必须添加@Validated注解 
@PostMapping("/edit/{id}")
public R<Void> update(@PathVariable String id, @Validated @RequestBody AiProfileTagUpdateFormDTO dto) {
    Assert.hasText(id, "主键标识不能为空！");
    aiProfileTagService.update(id, dto);
    return R.OK();
}

// 删除一条记录，使用POST方法
@PostMapping("/delete/{id}")
public R<Boolean> delete(@PathVariable String id) {
    return R.OK(aiProfileTagService.removeById(id));
}

```

### 2.4 联表查询，使用MybatisPlusJoin实现的示例
```java
// Service层中较复杂的一对多查询，使用MybatisPlusJoin实现
public List<SaSscChargeStationViewDTO> getSaSccInfo(String serAreaCode) {
    MPJLambdaWrapper<SaSscChargeStation> wrapper = new MPJLambdaWrapper<>(SaSscChargeStation.class)
            .selectAs(SaSscChargeStation::getStationId, SaSscChargeStationViewDTO::getStationId)
            //服务区_随手查_运营商
            .selectAssociation(SaSscOperator.class, SaSscChargeStationViewDTO::getSaSscOperator, operator -> operator
                    .id(SaSscOperator::getOperatorId, SaSscOperatorViewDTO::getOperatorId)
                    .result(SaSscOperator::getOperatorName, SaSscOperatorViewDTO::getOperatorName)
                    .result(SaSscOperator::getComments, SaSscOperatorViewDTO::getComments))
            //服务区_随手查_充电站设备
            .selectCollection(SaSscChargeEquipment.class, SaSscChargeStationViewDTO::getSaSscChargeEquipment, equipment -> equipment
                    .id(SaSscChargeEquipment::getEquipmentId, SaSscChargeEquipmentViewDTO::getEquipmentId)
                    .result(SaSscChargeEquipment::getEquipmentName, SaSscChargeEquipmentViewDTO::getEquipmentName)
                    .result(SaSscChargeEquipment::getStationId, SaSscChargeEquipmentViewDTO::getStationId)
                    //服务区_随手查_充电站设备接口
                    .collection(SaSscChargeConnector.class, SaSscChargeEquipmentViewDTO::getSaSscChargeConnectors, connector -> connector
                            .id(SaSscChargeConnector::getConnectorId, SaSscChargeConnectorViewDTO::getConnectorId)
                            .result(SaSscChargeConnector::getConnectorName, SaSscChargeConnectorViewDTO::getConnectorCode)
                            .result(SaSscChargeConnector::getEquipmentId, SaSscChargeConnectorViewDTO::getEquipmentId)
                            //服务区_随手查_计费时段明细表
                            .collection(SaSscChargeConnectorPolicy.class, SaSscChargeConnectorViewDTO::getSaSscChargeConnectorPolicys, policy -> policy
                                    .id(SaSscChargeConnectorPolicy::getPolicyId, SaSscChargeConnectorPolicyViewDTO::getPolicyId)
                                    .result(SaSscChargeConnectorPolicy::getStartTime, SaSscChargeConnectorPolicyViewDTO::getStartTime)
                                    .result(SaSscChargeConnectorPolicy::getConnectorId, SaSscChargeConnectorPolicyViewDTO::getConnectorId)
                            )
                    )
            )
            .innerJoin(SaSscOperator.class, SaSscOperator::getOperatorId, SaSscChargeStation::getOperatorId)
            .leftJoin(SaSscChargeEquipment.class, SaSscChargeEquipment::getStationId, SaSscChargeStation::getStationId)
            .leftJoin(SaSscChargeConnector.class, SaSscChargeConnector::getEquipmentId, SaSscChargeEquipment::getEquipmentId)
            .leftJoin(SaSscChargeConnectorPolicy.class, SaSscChargeConnectorPolicy::getConnectorId, SaSscChargeConnector::getConnectorId)
            .eq(SaSscChargeStation::getSerAreaCode, serAreaCode);
    return selectJoinList(SaSscChargeStationViewDTO.class, wrapper);
}
```
### 2.5 参数校验
```java
// 新增和修改语义不同时分别定义CreateFormDTO与UpdateFormDTO
@Data
public class AiProfileTagCreateFormDTO {

    /**
     * 标签名称
     */
    @NotBlank(message = "标签名称不能为空！")
    @Length(max = 100, message = "标签名称长度不能超过100位")
    private String tagName;

    /**
     * 标签描述
     */
    @NotBlank(message = "标签描述不能为空！")
    @Length(max = 200, message = "标签描述长度不能超过200位")
    private String tagDes;

    /**
     * 标签初始值
     */
    @Length(max = 10, message = "标签初始值长度不能超过10位")
    private String tagDefVal;

    /**
     * 顺序号
     */
    private Integer orderNo;
}

```
### 2.6 使用MapStruct进行实体和DTO之间的转换
```java
import com.guanwei.ai.dto.AiProfileRuleFormDTO;
import com.guanwei.ai.entity.AiProfileRule;
import com.guanwei.mybatis.mapstruct.MybatisPageBaseConvertMapper;
import org.mapstruct.Mapper;
import org.mapstruct.ReportingPolicy;

import static org.mapstruct.MappingConstants.ComponentModel.SPRING;
import static org.mapstruct.NullValuePropertyMappingStrategy.IGNORE;

// 请求体对象必须封装为XxxxFormDTO，并且根据数据库的字段要求添加必要的验证
@Mapper(componentModel = SPRING, nullValuePropertyMappingStrategy = IGNORE, unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface AiProfileRuleMapstruct extends MybatisPageBaseConvertMapper<AiProfileRuleFormDTO, AiProfileRule> {

}
```

## 三、命名规范

### 3.1 通用原则
- 所有命名**禁止使用拼音**（尤其禁止拼音与英文混用），须使用准确的英文单词。
- 命名应见名知意，避免无意义的缩写（如 `a`、`tmp`、`flag`）。
- 禁止使用Java关键字及保留字作为名称。

### 3.2 类与接口
| 类型 | 风格 | 示例                                          |
|------|------|---------------------------------------------|
| 普通类 | UpperCamelCase | `UserService`、`OrderController`             |
| 抽象类 | 以 `Abstract` 开头 | `AbstractBaseService`                       |
| 异常类 | 以 `Exception` 结尾 | `BusinessException`、`DataNotFoundException` |
| 测试类 | 以 `Test` 结尾 | `UserServiceTest`                           |
| 接口 | UpperCamelCase，不加 `I` 前缀 | `UserRepository`（Spring Data风格）             |
| 枚举类 | `Enum`前缀 + UpperCamelCase | `EnumOrderStatus`              |
| 实现类 | 接口名 + `Impl` | `UserServiceImpl`                           |

### 3.3 方法
- 使用 lowerCamelCase 风格。
- 动词或动词短语开头：`getUserById`、`calculateTotalPrice`、`isValidEmail`。
- 布尔返回值方法以 `is`/`has`/`can` 开头：`isActive()`、`hasPermission()`。

```java
// ✅ 正确
public User getUserById(Long userId) { ... }
public boolean isEmailValid(String email) { ... }
public void sendNotification(String message) { ... }

// ❌ 错误
public User get(Long id) { ... }       // 含义不清
public boolean emailValid(String e) { } // 参数名过短，方法名不规范
```

### 3.4 变量与常量
```java
// 常量：全大写 + 下划线分隔，必须用 static final 修饰
public static final int MAX_RETRY_COUNT = 3;
public static final String DEFAULT_CHARSET = "UTF-8";

// 普通变量：lowerCamelCase
private String userName;
private List<Order> orderList;

// 局部变量：同上
int pageSize = 10;
boolean isSuccess = false;

// ❌ 错误示例
int PAGESIZE = 10;         // 不是常量不应全大写
String user_name = "Tom";  // 变量不应使用下划线
```

### 3.5 包名
- 全小写并使用点分隔；单复数形式遵循项目现有包结构，避免同一概念混用两种形式。
- 结构建议：`com.公司名.项目名.模块名.层级`

```
com.guanwei.tles.oles.warning.service
com.guanwei.tles.oles.warning.controller
com.guanwei.tles.oles.warning.utils
```

---

## 四、代码格式规范

### 4.1 基本格式
- 缩进：4个空格（禁止Tab字符）。
- 行宽以可读性为准，120个字符仅作为参考，不是强制换行阈值。
- 方法签名、参数列表、注解和简单方法调用即使略超120个字符，也优先保持单行。
- 仅当一行明显过长、结构复杂或严重影响阅读时才换行。
- 修改已有代码时保留原有换行风格，不要仅为满足行宽产生无业务意义的格式化差异。
- 左大括号 `{` 不换行，右大括号 `}` 单独占一行。

### 4.2 空行与空格
- 方法之间保留一个空行。
- 运算符两侧各加一个空格：`a + b`、`x == y`。
- 方法参数逗号后加空格：`method(a, b, c)`。
- 类型强转后加空格：`(String) object`。

### 4.3 注释规范
```java
/**
 * 类级别注释：描述类的职责与用途。
 * 禁止在代码注释中使用中文与英文混合的拼写。
 *
 * @author 张三
 * @date 2024-01-01
 */
public class OrderService {

    /**
     * 根据用户ID获取订单列表。
     *
     * @param userId  用户ID，不能为null
     * @param status  订单状态，null表示查询全部
     * @return 订单列表，若无数据返回空列表（不返回null）
     * @throws BusinessException 当用户不存在时抛出
     */
    public List<Order> getOrdersByUserId(Long userId, EnumOrderStatus status) {
        // 单行注释：解释为什么，而不是解释做什么
        // 此处过滤已删除的订单，逻辑删除字段 deleted=1 表示已删除
        return orderRepository.findByUserIdAndStatus(userId, status);
    }
}
```

**注释原则：**
- 所有的类、属性、方法需要添加注释
- TODO 注释须写明原因及负责人：`// TODO(张三): 待接入第三方支付后移除此逻辑`

---

## 五、面向对象设计规范

### 5.1 类设计
```java
// ✅ 推荐：使用 Lombok 减少样板代码
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserViewDTO {
    private Long id;
    private String username;
    private String email;
}

// POJO类字段不要设置默认值（使用者决定默认值）
// ❌ 错误
private boolean deleted = false; // 不应在POJO中设置默认值
```

### 5.2 接口与实现分离
```java
// ✅ 接口定义行为
public interface PaymentService {
    PaymentResult pay(PaymentRequest request);
}

// ✅ 实现类专注于实现细节
@Service
@Slf4j
public class AlipayServiceImpl implements PaymentService {

    @Override
    public PaymentResult pay(PaymentRequest request) {
        log.info("发起支付宝支付, orderId={}, amount={}", 
                 request.getOrderId(), request.getAmount());
        // 具体实现...
    }
}
```

### 5.3 禁止使用魔法值
```java
// ❌ 错误：魔法数字与魔法字符串
if (user.getStatus() == 1) { ... }
if ("ADMIN".equals(user.getRole())) { ... }

// ✅ 正确：使用枚举或常量
if (user.getStatus() == EnumUserStatus.ACTIVE.getCode()) { ... }
if (EnumUserRole.ADMIN.name().equals(user.getRole())) { ... }
```

---


## 六、并发与线程安全

### 6.1 线程池规范
```java
// ✅ 使用ThreadPoolExecutor，禁止使用Executors工厂方法
// Executors.newFixedThreadPool 使用无界队列，可能导致OOM
ThreadPoolExecutor executor = new ThreadPoolExecutor(
        5,                                // corePoolSize
        20,                               // maximumPoolSize
        60L, TimeUnit.SECONDS,            // keepAliveTime
        new LinkedBlockingQueue<>(1000),  // 有界队列，避免OOM
        new ThreadFactoryBuilder()
                .setNameFormat("order-task-%d")  // 线程命名，便于排查
                .setDaemon(false)
                .build(),
        new ThreadPoolExecutor.CallerRunsPolicy() // 拒绝策略
);

// ✅ Spring环境推荐使用@Async + 配置ThreadPoolTaskExecutor
@Configuration
@EnableAsync
public class AsyncConfig {
    @Bean("taskExecutor")
    public ThreadPoolTaskExecutor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(500);
        executor.setThreadNamePrefix("async-task-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }
}
```

### 6.2 线程安全
```java
// ✅ 优先使用并发容器
ConcurrentHashMap<String, Object> concurrentMap = new ConcurrentHashMap<>();
CopyOnWriteArrayList<String> cowList = new CopyOnWriteArrayList<>();

// ✅ 原子操作用AtomicXxx
AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet();

// ✅ ThreadLocal使用后必须remove，防止内存泄漏
private static final ThreadLocal<UserContext> USER_CONTEXT = new ThreadLocal<>();

public void setContext(UserContext context) {
    USER_CONTEXT.set(context);
}

public void clearContext() {
    USER_CONTEXT.remove(); // 必须在请求结束后调用
}

// ❌ 禁止在多线程环境下使用非线程安全类
// SimpleDateFormat 非线程安全，禁止作为共享变量
// ✅ 替代方案
DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"); // 线程安全
```

---

## 七、日志规范

### 7.1 基本规则
```java
@Slf4j // Lombok注解，自动生成 log 变量
public class OrderService {

    public void processOrder(Long orderId) {
        // ✅ 使用占位符，避免字符串拼接的性能损耗
        log.info("开始处理订单, orderId={}", orderId);

        // ✅ 日志分级使用
        // 序列化对象前先判断日志级别，并确保对象中不含密码、Token等敏感字段
        if (log.isDebugEnabled()) {
            log.debug("订单详情: {}", JSON.toJSONString(order));
        }
        log.info("订单状态变更: {} -> {}", oldStatus, newStatus); // 关键业务流程
        log.warn("库存不足，降级处理: productId={}", productId);    // 警告，不影响主流程
        log.error("订单支付失败: orderId={}", orderId, e);          // 错误，须传入异常对象

        // ❌ 禁止：字符串拼接
        log.info("开始处理订单, orderId=" + orderId); // 无论是否输出都会拼接字符串
    }
}
```

### 7.2 日志内容规范
```java
// ✅ 关键业务节点必须打印日志
log.info("[支付] 发起支付请求, orderId={}, amount={}, channel={}", orderId, amount, channel);
log.info("[支付] 支付结果返回, orderId={}, status={}, transactionId={}", orderId, status, transactionId);

// ✅ 异常日志必须打印完整堆栈
log.error("[支付] 调用支付宝接口异常, orderId={}", orderId, e); // 最后一个参数传异常

// ❌ 禁止输出敏感信息到日志
log.info("用户登录: username={}, password={}", username, password); // 密码禁止输出
log.info("支付信息: cardNo={}", cardNo); // 银行卡号禁止输出
```

---

## 八、代码审查检查清单

在提交代码前，自查以下各项：

**命名与格式**
- [ ] 满足一级军规
- [ ] 类、方法、变量命名使用英文且见名知意
- [ ] 无魔法值，常量已定义为枚举或 `static final`
- [ ] 代码格式已格式化，无多余空行/空格

**健壮性**
- [ ] 满足一级军规
- [ ] 所有外部输入均有校验
- [ ] 集合参数/返回值已做空判断，不返回 `null`
- [ ] 仅在能够恢复、转换异常或补充必要上下文时捕获异常
- [ ] 未吞掉异常，未在多个层级重复记录同一异常
- [ ] 可统一处理的异常交由全局异常处理器
- [ ] 资源（IO、连接）已在 `finally` 或 `try-with-resources` 中关闭

**性能**
- [ ] 满足一级军规
- [ ] 无循环内数据库查询（N+1问题）
- [ ] 集合初始化已指定合理容量
- [ ] 线程池使用 `ThreadPoolExecutor`，非 `Executors` 工厂方法

**日志与注释**
- [ ] 满足一级军规
- [ ] 关键业务节点有日志记录
- [ ] 日志使用占位符，无字符串拼接
- [ ] 日志中无敏感信息（密码、卡号等）
- [ ] 公共方法有JavaDoc注释

**安全**
- [ ] 满足一级军规
- [ ] 无SQL注入问题
- [ ] 无SQL拼接，均使用参数化查询

---

## 九、快速参考

| 场景      | 推荐方案                                                        |
|---------|-----------------------------------------------------------------|
| 金额计算    | `BigDecimal`，禁用 `double`/`float`                             |
| 字符串判空   | `EmptyUtil.isNotEmpty()`，禁用 `== null \|\| isEmpty()`         |
| 集合判空    | `EmptyUtil.isEmpty()`，禁用 `== null \|\| size() == 0`          |
| JSON序列化 | `Fastjson2`（统一项目内使用同一框架）                           |
| HTTP客户端 | `RestTemplate`（同步）/ `WebClient`（响应式/异步）              |
| 对象拷贝    | `MapStruct`（推荐，类型安全）                                   |
| 唯一ID生成  | 雪花算法 / `UUID.randomUUID()` / 数据库自增（选其一，项目统一） |
| 枚举比较    | `==` 比较，不用 `equals()`                                      |
| 字符串比较   | `"constant".equals(variable)`，常量在前防NPE                    |
| 工具类     | 推荐使用`Hutool`工具类                                          |
