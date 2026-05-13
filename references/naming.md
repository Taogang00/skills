# 命名规范（参考阿里巴巴Java开发手册）

## 1. 通用命名原则

| 规则ID | 级别 | 规则描述 |
|---|---|---|
| N-001 | 【强制】 | 代码中的命名均不能以下划线或美元符号开始，也不能以下划线或美元符号结束 |
| N-002 | 【强制】 | 代码中的命名严禁使用拼音与英文混合的方式，更不允许直接使用中文的方式 |
| N-003 | 【强制】 | 类名使用 `UpperCamelCase` 风格，但以下情形例外：DO / BO / DTO / VO / AO / PO / UID 等 |
| N-004 | 【强制】 | 方法名、参数名、成员变量、局部变量都统一使用 `lowerCamelCase` 风格 |
| N-005 | 【强制】 | 常量命名全部大写，单词间用下划线隔开，力求语义表达完整清楚 |
| N-006 | 【强制】 | 抽象类命名使用 `Abstract` 或 `Base` 开头；异常类命名使用 `Exception` 结尾；测试类命名以它要测试的类的名称开始，以 `Test` 结尾 |
| N-007 | 【强制】 | 类型与中括号紧挨相连来表示数组：`String[] args`（禁止：`String args[]`） |
| N-008 | 【强制】 | POJO类中布尔类型变量都不要加 `is` 前缀，否则部分框架解析会引起序列化错误 |
| N-009 | 【强制】 | 包名统一使用小写，点分隔符之间有且仅有一个自然语义的英语单词 |
| N-010 | 【强制】 | 避免在子父类的成员变量之间、或者不同代码块的局部变量之间采用完全相同的命名，使可读性降低 |

## 2. 包名规范

```
com.guanwei.{业务线}.[子业务线].[模块名]
```

**标准分层包结构：**
```
com.guanwei.tles.oles.warning
├── controller      # 控制层（REST接口）
├── service         # 业务逻辑层
│   └── impl        # 业务实现
├── mapper          # 数据访问层（MyBatis）/ repository（JPA）
├── entity          # 数据库实体（PO）
├── query           # 数据查询对象
├── enums           # 枚举类
├── utils           # 工具类
├── constant        # 常量类
├── dto             # 数据传输对象
├── config          # 配置类
└── exception       # 自定义异常
```

## 3. 类命名规范

| 场景             | 命名方式 | 示例                                            |
|----------------|---|-----------------------------------------------|
| 业务实体（数据库映射）    | `{业务}` | `SysUser`                                     |
| 数据传输对象（接收请求参数） | `{业务}DTO` | `CreateOrderDTO`          |
| 数据查询对象（接收请求参数） | `{业务}Query` | `OrderQuery`                                |
| 服务接口           | `{业务}Service` | `OrderService`                                |
| 服务实现           | `{业务}ServiceImpl` | `OrderServiceImpl`                            |
| 控制器            | `{业务}Controller` | `OrderController`                             |
| 数据访问           | `{业务}Mapper` / `{业务}Repository` | `OrderMapper`                                 |
| 工具类            | `{功能}Utils` / `{功能}Helper` | `DateUtils`, `StringHelper`                   |
| 配置类            | `{功能}Config` / `{功能}Configuration` | `RedisConfig`, `SwaggerConfiguration`         |
| 常量类            | `{模块}Constants` | `OrderConstants`, `CommonConstants`           |
| 枚举类            | `Enum{业务}{属性}` | `EnumOrderStatus`, `EnumUserType`             |
| 异常类            | `{业务}Exception` | `OrderNotFoundException`, `BusinessException` |
| 抽象类            | `Abstract{功能}` / `Base{功能}` | `AbstractValidator`, `BaseController`         |

## 4. 方法命名规范

| 场景 | 动词前缀 | 示例 |
|---|---|---|
| 获取单个对象 | `get` | `getUser()`, `getOrderById()` |
| 获取多个对象 | `list` / `query` | `listUsers()`, `queryOrdersByStatus()` |
| 统计数量 | `count` | `countActiveUsers()` |
| 插入/保存 | `save` / `insert` / `add` | `saveOrder()`, `addUser()` |
| 删除 | `remove` / `delete` | `removeById()`, `deleteExpiredOrders()` |
| 修改 | `update` / `modify` | `updateUserInfo()`, `modifyOrderStatus()` |
| 批量操作 | `batch{动词}` | `batchInsert()`, `batchUpdate()` |
| 初始化 | `init` | `initConfig()` |
| 判断/校验 | `is` / `check` / `validate` | `isValid()`, `checkPermission()`, `validateParams()` |
| 转换 | `to` / `convert` | `toVO()`, `convertToDTO()` |
| 发送 | `send` | `sendEmail()`, `sendSms()` |

## 5. 变量命名规范

```java
// ✅ 正确示例
private static final int MAX_RETRY_COUNT = 3;
private static final String DEFAULT_CHARSET = "UTF-8";
private boolean deleteFlag;          // POJO中不用 isDeleted
private boolean enabled;             // 不用 isEnabled
private String userName;
private List<OrderVO> orderList;
private Map<String, UserVO> userMap;

// ❌ 错误示例
private static final int maxRetryCount = 3;   // 常量要全大写
private boolean isDeleted;                     // POJO布尔不加is前缀
private String UserName;                       // 变量不能大写开头
int a, b, c;                                   // 无意义命名
String $name;                                  // 不能以$开头
```

## 6. 数据库字段命名规范

| 规则 | 说明 | 示例 |
|---|---|---|
| 全小写 + 下划线分隔 | `snake_case` | `user_name`, `create_time` |
| 禁止使用保留字 | 如 `desc`, `range`, `match` 等 | 改用 `description`, `range_val` |
| 主键命名 | 统一为 `id` | `id BIGINT UNSIGNED` |
| 外键命名 | `{关联表}_id` | `user_id`, `order_id` |
| 时间字段 | `create_time`, `update_time`, `delete_time` | 统一使用 `DATETIME` 类型 |
| 逻辑删除 | `is_deleted` TINYINT(1) | 0-未删除，1-已删除 |
| 状态字段 | `{业务}_status` | `order_status`, `pay_status` |
| 布尔字段 | `is_{描述}` | `is_enabled`, `is_deleted` |
| 金额字段 | 使用 `DECIMAL(18,2)`，单位：元 | `pay_amount` |

## 7. 接口与实现命名

```java
// 接口：不加 I 前缀（阿里规范），直接用业务名
public interface UserService { ... }
public interface OrderRepository { ... }

// 实现类：接口名 + Impl
public class UserServiceImpl implements UserService { ... }

// 有多个实现时，用场景区分
public class CacheUserServiceImpl implements UserService { ... }
public class DbUserServiceImpl implements UserService { ... }
```
