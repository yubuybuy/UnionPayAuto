// ========================================
// 云闪付高级Hook - 自动化领券
// ========================================
//
// 功能：
// 1. 自动检测优惠券页面
// 2. 自动点击领券按钮
// 3. 自动处理验证码（用户输入距离）
// 4. 记录所有bhv参数
//
// ========================================

console.log("🚀 云闪付自动化Hook加载中...\n");

if (ObjC.available) {

    // ========================================
    // 配置
    // ========================================

    var config = {
        autoClick: true,           // 自动点击领券按钮
        autoRetry: true,           // 自动重试
        logNetwork: true,          // 记录网络请求
        saveBhv: true,             // 保存bhv到文件
        bhvHistory: [],            // bhv历史记录
        maxRetry: 10,              // 最大重试次数
        retryCount: 0              // 当前重试次数
    };


    // ========================================
    // 工具函数
    // ========================================

    function log(msg, type) {
        var prefix = {
            'info': '[ℹ️]',
            'success': '[✅]',
            'error': '[❌]',
            'warning': '[⚠️]',
            'hook': '[🎯]'
        }[type] || '[*]';

        console.log(prefix + " " + msg);
    }

    function showAlert(title, message) {
        ObjC.schedule(ObjC.mainQueue, function() {
            var UIAlertView = ObjC.classes.UIAlertView;
            var alert = UIAlertView.alloc().initWithTitle_message_delegate_cancelButtonTitle_otherButtonTitles_(
                title, message, null, "确定", null
            );
            alert.show();
        });
    }

    function saveBhv(bhv) {
        if (!config.saveBhv) return;

        var timestamp = new Date().toISOString();
        config.bhvHistory.push({
            timestamp: timestamp,
            bhv: bhv,
            length: bhv.length
        });

        log("已保存bhv (" + config.bhvHistory.length + ")", 'info');

        // 通过send发送到Python端保存
        send({
            type: 'bhv_captured',
            timestamp: timestamp,
            bhv: bhv
        });
    }


    // ========================================
    // Hook: 验证码处理
    // ========================================

    try {
        var UPWSliderCaptchaView = ObjC.classes.UPWSliderCaptchaView;

        if (UPWSliderCaptchaView) {
            log("找到 UPWSliderCaptchaView", 'success');

            // Hook 1: verifySliderCaptcha:
            Interceptor.attach(
                UPWSliderCaptchaView['- verifySliderCaptcha:'].implementation,
                {
                    onEnter: function(args) {
                        log("验证码验证被调用", 'hook');

                        var param = new ObjC.Object(args[2]);
                        log("参数类型: " + param.$className, 'info');

                        // 如果是字典，提取bhv
                        if (param.$className.indexOf('Dictionary') !== -1) {
                            var allKeys = param.allKeys();

                            for (var i = 0; i < allKeys.count(); i++) {
                                var key = allKeys.objectAtIndex_(i).toString();
                                var value = param.objectForKey_(allKeys.objectAtIndex_(i));

                                log("  " + key + " = " + value, 'info');

                                // 提取bhv
                                if (key.toLowerCase().indexOf('bhv') !== -1) {
                                    var bhv = value.toString();
                                    log("🔑 捕获到bhv!", 'success');
                                    log("🔑 长度: " + bhv.length, 'info');
                                    log("🔑 内容: " + bhv.substring(0, 100) + "...", 'info');

                                    saveBhv(bhv);
                                }
                            }
                        }
                    },
                    onLeave: function(retval) {
                        log("验证码验证完成", 'success');
                    }
                }
            );

            // Hook 2: handleCaptchaResult:
            Interceptor.attach(
                UPWSliderCaptchaView['- handleCaptchaResult:'].implementation,
                {
                    onEnter: function(args) {
                        var result = new ObjC.Object(args[2]);
                        log("收到验证码结果", 'hook');

                        if (result.$className.indexOf('Dictionary') !== -1) {
                            var code = result.objectForKey_('resCode');
                            var msg = result.objectForKey_('resMsg');

                            if (code && code.toString() === '0000') {
                                log("验证码验证成功!", 'success');
                                showAlert("成功", "验证码验证成功");

                                // 发送成功通知
                                send({ type: 'captcha_success' });
                            } else {
                                log("验证码验证失败: " + (msg || '未知错误'), 'error');

                                if (config.autoRetry && config.retryCount < config.maxRetry) {
                                    config.retryCount++;
                                    log("准备第 " + config.retryCount + " 次重试", 'warning');
                                }
                            }
                        }
                    }
                }
            );

            log("验证码Hook设置完成", 'success');

        } else {
            log("未找到 UPWSliderCaptchaView", 'error');
        }
    } catch (e) {
        log("验证码Hook失败: " + e, 'error');
    }


    // ========================================
    // Hook: 网络请求监控
    // ========================================

    if (config.logNetwork) {
        try {
            var NSURLSession = ObjC.classes.NSURLSession;

            Interceptor.attach(
                NSURLSession['- dataTaskWithRequest:completionHandler:'].implementation,
                {
                    onEnter: function(args) {
                        var request = new ObjC.Object(args[2]);
                        var url = request.URL().toString();

                        // 只记录关键API
                        var keywords = [
                            'captcha', 'verify', 'vfy',
                            'coupon', 'acquire',
                            '/session/', 'initses'
                        ];

                        var isRelevant = false;
                        for (var i = 0; i < keywords.length; i++) {
                            if (url.indexOf(keywords[i]) !== -1) {
                                isRelevant = true;
                                break;
                            }
                        }

                        if (isRelevant) {
                            log("🌐 网络请求: " + url, 'info');

                            var method = request.HTTPMethod();
                            if (method) {
                                log("   Method: " + method, 'info');
                            }

                            // 发送到Python端
                            send({
                                type: 'network_request',
                                url: url,
                                method: method ? method.toString() : 'GET'
                            });
                        }
                    }
                }
            );

            log("网络监控Hook设置完成", 'success');

        } catch (e) {
            log("网络Hook失败: " + e, 'error');
        }
    }


    // ========================================
    // Hook: UI按钮点击
    // ========================================

    try {
        var UIButton = ObjC.classes.UIButton;

        // Hook sendActionsForControlEvents:
        Interceptor.attach(
            UIButton['- sendActionsForControlEvents:'].implementation,
            {
                onEnter: function(args) {
                    var button = new ObjC.Object(args[0]);
                    var title = button.currentTitle();

                    if (title) {
                        var titleStr = title.toString();

                        // 检测领券按钮
                        if (titleStr.indexOf('领取') !== -1 ||
                            titleStr.indexOf('抢') !== -1 ||
                            titleStr.indexOf('立即') !== -1) {

                            log("🔘 检测到按钮点击: " + titleStr, 'hook');

                            send({
                                type: 'button_clicked',
                                title: titleStr
                            });
                        }
                    }
                }
            }
        );

        log("UI监控Hook设置完成", 'success');

    } catch (e) {
        log("UI Hook失败: " + e, 'error');
    }


    // ========================================
    // RPC 导出函数
    // ========================================

    rpc.exports = {
        // 获取bhv历史
        getBhvHistory: function() {
            return config.bhvHistory;
        },

        // 触发领券按钮点击
        clickAcquireButton: function() {
            log("RPC: 触发领券按钮点击", 'info');

            ObjC.schedule(ObjC.mainQueue, function() {
                // 遍历所有窗口查找按钮
                var windows = ObjC.classes.UIApplication.sharedApplication().windows();

                for (var i = 0; i < windows.count(); i++) {
                    var window = windows.objectAtIndex_(i);
                    findAndClickButton(window);
                }
            });

            return true;
        },

        // 设置配置
        setConfig: function(key, value) {
            if (config.hasOwnProperty(key)) {
                config[key] = value;
                log("配置已更新: " + key + " = " + value, 'success');
                return true;
            }
            return false;
        },

        // 获取配置
        getConfig: function() {
            return config;
        }
    };

    // 辅助函数：查找并点击按钮
    function findAndClickButton(view) {
        var subviews = view.subviews();
        if (!subviews) return false;

        for (var i = 0; i < subviews.count(); i++) {
            var subview = subviews.objectAtIndex_(i);

            if (subview.isKindOfClass_(ObjC.classes.UIButton.class_())) {
                var button = subview;
                var title = button.currentTitle();

                if (title) {
                    var titleStr = title.toString();

                    if (titleStr.indexOf('领取') !== -1 ||
                        titleStr.indexOf('抢') !== -1) {

                        log("找到按钮: " + titleStr, 'success');
                        button.sendActionsForControlEvents_(64);  // UIControlEventTouchUpInside
                        return true;
                    }
                }
            }

            // 递归查找
            if (findAndClickButton(subview)) {
                return true;
            }
        }

        return false;
    }


    // ========================================
    // 初始化完成
    // ========================================

    console.log("\n" + "=".repeat(60));
    log("云闪付自动化Hook加载完成!", 'success');
    console.log("=".repeat(60));

    console.log("\n可用的RPC函数:");
    console.log("  - getBhvHistory()       获取bhv历史");
    console.log("  - clickAcquireButton()  触发领券按钮");
    console.log("  - setConfig(key, val)   设置配置");
    console.log("  - getConfig()           获取配置");

    console.log("\n当前配置:");
    console.log(JSON.stringify(config, null, 2));
    console.log("");

} else {
    console.log("[!] Objective-C Runtime 不可用");
}
