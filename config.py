# 云闪付自动领券配置文件

# 活动配置
ACTIVITY_ID = "17"
CATE_CODE = "A07"
AREA_CODE = "510099"  # 地区代码（成都）

# 地理位置
LONGITUDE = "103.3986303710937"
LATITUDE = "29.87659369574653"

# 设备信息（需要从HAR文件中提取你自己的）
DEVICE_ID = "你的设备ID"
DFP_ID = "你的设备指纹ID"

# Cookie（从HAR文件中提取）
COOKIES = {
    # "key": "value"
}

# 请求头（从HAR文件中提取特殊字段）
CUSTOM_HEADERS = {
    # "Authorization": "Bearer xxx"
}

# 运行配置
MAX_RETRY = 100              # 最大重试次数
INIT_SESSION_INTERVAL = 1.0  # 会话轮询间隔（秒）
ACQUIRE_INTERVAL = 5.0       # 领券失败后等待时间（秒）
CAPTCHA_TIMEOUT = 30         # 验证码处理超时时间（秒）

# 多账号配置（可选）
MULTI_ACCOUNT = False
ACCOUNTS = [
    {
        "name": "账号1",
        "device_id": "设备ID1",
        "dfp_id": "设备指纹1",
        "cookies": {},
    },
    # {
    #     "name": "账号2",
    #     "device_id": "设备ID2",
    #     "dfp_id": "设备指纹2",
    #     "cookies": {},
    # },
]

# 打码平台配置（如果使用第三方打码服务）
CAPTCHA_SERVICE = {
    "enabled": False,
    "type": "ddddocr",  # ddddocr, yescaptcha, 2captcha
    "api_key": "",
}

# 通知配置
NOTIFICATION = {
    "enabled": False,
    "type": "wechat",  # wechat, email, webhook
    "webhook_url": "",  # 企业微信/钉钉webhook地址
}

# 调试模式
DEBUG = True
SAVE_CAPTCHA_IMAGE = True  # 保存验证码图片用于调试
