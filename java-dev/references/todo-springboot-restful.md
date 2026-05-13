# Spring Boot RESTful API 设计规范

## 1. URL 设计规范

### 核心原则

| 规则ID | 级别 | 规则 |
|---|---|---|
| R-001 | 【强制】 | URL 使用名词复数，代表资源集合，禁止使用动词 |
| R-002 | 【强制】 | URL 全部小写，多个单词用连字符 `-` 分隔，禁用下划线和驼峰 |
| R-003 | 【强制】 | API 版本号放在 URL 路径中：`/api/v1/`，不放 Header |
| R-004 | 【强制】 | 资源之间的层级关系用 `/` 表达，最多 3 层，超过则考虑独立资源 |
| R-005 | 【强制】 | 过滤/分页/排序参数放 Query String，不放 URL 路径 |
| R-006 | 【推荐】 | URL 末尾不加斜杠 `/` |

```
# ✅ 正确
GET    /api/v1/users
GET    /api/v1/users/{userId}
GET    /api/v1/users/{userId}/orders
GET    /api/v1/orders?status=paid&page=1&size=20
POST   /api/v1/users
PUT    /api/v1/users/{userId}
PATCH  /api/v1/users/{userId}/status
DELETE /api/v1/users/{userId}

# ❌ 错误
GET /api/v1/getUsers           # 使用了动词
GET /api/v1/user               # 单数
GET /api/v1/users/getUserById  # URL含动词
POST /api/v1/users/create      # 冗余动词，POST本身表示创建
GET /api/v1/userOrders/{id}    # 驼峰，应用连字符 user-orders
```

### HTTP 方法语义

| 方法 | 语义 | 幂等性 | 请求体 |
|---|---|---|---|
| `GET` | 查询资源，不修改状态 | 是 | 无 |
| `POST` | 创建新资源 / 触发复杂操作 | 否 | 有 |
| `PUT` | 全量更新资源（替换整个资源） | 是 | 有 |
| `PATCH` | 部分更新资源（只更新指定字段） | 否 | 有 |
| `DELETE` | 删除资源 | 是 | 无 |

## 2. 统一响应体规范

### 标准响应结构

```java
package com.guanwei.core.utils.result;

import lombok.Data;

import java.io.Serializable;

/**
 * 自定义返回的数据格式
 *
 * @author taogang
 * @date 2021/09/06
 */
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

### 分页响应结构

```java
package com.guanwei.core.utils.result;

import lombok.Data;

import java.util.List;

/**
 * 分页的返回结果
 *
 * @author TaoGang
 **/
@Data
public class PageResult<T> {

    /**
     * 数据
     */
    private List<T> data;

    /**
     * 总记录数
     */
    private int records;

    /**
     * 当前页
     */
    private int page;

    /**
     * 每页行数
     */
    private int pageSize;

    /**
     * 总页数
     */
    private int total;

    public PageResult() {
    }

    public PageResult(int page, int pageSize) {
        this.page = page;
        this.pageSize = pageSize;
    }

    public PageResult(List<T> data, int records, int page, int pageSize, int total) {
        this.data = data;
        this.records = records;
        this.page = page;
        this.pageSize = pageSize;
        this.total = total;
    }

    @SuppressWarnings("unused")
    public int getTotal() {
        if (this.pageSize > 0) {
            if (this.records % this.pageSize == 0) {
                return (this.records / this.pageSize);
            } else {
                return (this.records / this.pageSize) + 1;
            }
        }
        return 0;
    }

}

```

### HTTP 状态码使用

| 状态码 | 场景 |
|---|---|
| `200 OK` | 成功（GET/PUT/PATCH/DELETE） |
| `201 Created` | 资源创建成功（POST） |
| `204 No Content` | 成功但无返回体（DELETE） |
| `400 Bad Request` | 参数校验失败、请求格式错误 |
| `401 Unauthorized` | 未认证（未登录/Token无效） |
| `403 Forbidden` | 已认证但无权限 |
| `404 Not Found` | 资源不存在 |
| `409 Conflict` | 资源冲突（如重复创建） |
| `500 Internal Server Error` | 服务端未知错误 |

## 3. Controller 层规范

```java
@RestController
@RequestMapping("/api/v1/users")
@Validated                           // 开启参数校验
@Slf4j
public class UserController {

    private final UserService userService;

    // ✅ 构造器注入，不用 @Autowired 字段注入
    public UserController(UserService userService) {
        this.userService = userService;
    }

    /**
     * 分页查询用户列表
     */
    @GetMapping
    public ApiResponse<PageResponse<UserVO>> listUsers(
            @Valid UserQueryRequest request) {
        return ApiResponse.success(userService.listUsers(request));
    }

    /**
     * 根据ID查询用户详情
     */
    @GetMapping("/{userId}")
    public ApiResponse<UserVO> getUserById(
            @PathVariable @Positive Long userId) {
        return ApiResponse.success(userService.getUserById(userId));
    }

    /**
     * 创建用户
     */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ApiResponse<UserVO> createUser(
            @RequestBody @Valid CreateUserRequest request) {
        return ApiResponse.success(userService.createUser(request));
    }

    /**
     * 全量更新用户
     */
    @PutMapping("/{userId}")
    public ApiResponse<UserVO> updateUser(
            @PathVariable @Positive Long userId,
            @RequestBody @Valid UpdateUserRequest request) {
        return ApiResponse.success(userService.updateUser(userId, request));
    }

    /**
     * 部分更新用户状态
     */
    @PatchMapping("/{userId}/status")
    public ApiResponse<Void> updateUserStatus(
            @PathVariable @Positive Long userId,
            @RequestBody @Valid UpdateStatusRequest request) {
        userService.updateUserStatus(userId, request.getStatus());
        return ApiResponse.success(null);
    }

    /**
     * 删除用户
     */
    @DeleteMapping("/{userId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteUser(@PathVariable @Positive Long userId) {
        userService.deleteUser(userId);
    }
}
```

## 4. 参数校验规范

### 常用校验注解

```java
@Data
public class CreateUserRequest {

    @NotBlank(message = "用户名不能为空")
    @Length(min = 2, max = 32, message = "用户名长度必须在2-32位之间")
    @Pattern(regexp = "^[a-zA-Z0-9_]+$", message = "用户名只能包含字母、数字和下划线")
    private String userName;

    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String email;

    @NotNull(message = "年龄不能为空")
    @Min(value = 0, message = "年龄不能小于0")
    @Max(value = 150, message = "年龄不能大于150")
    private Integer age;

    @NotNull(message = "用户类型不能为空")
    private UserTypeEnum userType;
}
```

## 5. Service 层规范

```java
public interface UserService {
    PageResponse<UserVO> listUsers(UserQueryRequest request);
    UserVO getUserById(Long userId);
    UserVO createUser(CreateUserRequest request);
    UserVO updateUser(Long userId, UpdateUserRequest request);
    void updateUserStatus(Long userId, Integer status);
    void deleteUser(Long userId);
}

@Service
@Slf4j
@Transactional(rollbackFor = Exception.class)  // 事务注解加在实现类
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;
    private final UserConverter userConverter;  // 对象转换器（MapStruct）

    public UserServiceImpl(UserMapper userMapper, UserConverter userConverter) {
        this.userMapper = userMapper;
        this.userConverter = userConverter;
    }

    @Override
    @Transactional(readOnly = true)  // 查询方法标注只读事务
    public UserVO getUserById(Long userId) {
        UserPO userPO = userMapper.selectById(userId);
        if (userPO == null) {
            throw new ResourceNotFoundException("用户不存在，userId=" + userId);
        }
        return userConverter.toVO(userPO);
    }

    @Override
    public UserVO createUser(CreateUserRequest request) {
        // 1. 业务校验
        if (userMapper.existsByEmail(request.getEmail())) {
            throw new BusinessException(ErrorCode.EMAIL_ALREADY_EXISTS);
        }
        // 2. 转换并保存
        UserPO userPO = userConverter.toPO(request);
        userPO.setCreateTime(LocalDateTime.now());
        userMapper.insert(userPO);
        // 3. 返回视图对象
        return userConverter.toVO(userPO);
    }
}
```
