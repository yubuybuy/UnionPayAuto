// ========================================
// 云闪付验证码动态分析 - Frida脚本
// ========================================
//
// 使用方法：
// 1. USB连接手机
// 2. 打开云闪付APP
// 3. 运行: frida -U -n 云闪付 -l frida_captcha_observer.js
// 4. 触发验证码，观察输出
//
// ========================================

console.log("[*] ========================================");
console.log("[*] 云闪付验证码观察器已加载");
console.log("[*] ========================================\n");

if (ObjC.available) {

    // ================================================
    // 第一步：列出所有验证码相关的类
    // ================================================
    console.log("[1] 🔍 搜索验证码相关类...\n");

    var captchaClasses = [];
    for (var className in ObjC.classes) {
        if (className.toLowerCase().indexOf('captcha') !== -1 ||
            className.toLowerCase().indexOf('slider') !== -1 ||
            className.toLowerCase().indexOf('verify') !== -1) {
            captchaClasses.push(className);
        }
    }

    console.log("[+] 找到 " + captchaClasses.length + " 个相关类:\n");
    captchaClasses.forEach(function(name) {
        console.log("    ✓ " + name);
    });


    // ================================================
    // 第二步：Hook核心验证码类
    // ================================================
    console.log("\n[2] 🎯 开始Hook验证码类...\n");

    // Hook UPWSliderCaptchaView
    try {
        var UPWSliderCaptchaView = ObjC.classes.UPWSliderCaptchaView;

        if (UPWSliderCaptchaView) {
            console.log("[+] ✅ 找到 UPWSliderCaptchaView");

            // 列出所有方法
            console.log("[+] 方法列表:");
            var methods = UPWSliderCaptchaView.$ownMethods;
            methods.forEach(function(method) {
                console.log("    - " + method);
            });

            // Hook verifySliderCaptcha: 方法
            if (UPWSliderCaptchaView['- verifySliderCaptcha:']) {
                console.log("\n[+] 🔗 Hook verifySliderCaptcha: ...");

                Interceptor.attach(
                    UPWSliderCaptchaView['- verifySliderCaptcha:'].implementation,
                    {
                        onEnter: function(args) {
                            console.log("\n" + "=".repeat(60));
                            console.log("🎯 [verifySliderCaptcha] 被调用！");
                            console.log("=".repeat(60));

                            // args[0] = self
                            // args[1] = selector
                            // args[2] = 第一个参数

                            var param = new ObjC.Object(args[2]);
                            console.log("参数类型:", param.$className);
                            console.log("参数内容:", param.toString());

                            // 如果是NSDictionary，遍历所有键值对
                            if (param.$className === '__NSDictionaryM' ||
                                param.$className === '__NSDictionaryI' ||
                                param.$className === 'NSDictionary') {

                                console.log("\n📋 字典内容:");
                                var keys = param.allKeys();
                                for (var i = 0; i < keys.count(); i++) {
                                    var key = keys.objectAtIndex_(i);
                                    var value = param.objectForKey_(key);
                                    console.log("  " + key + ": " + value);

                                    // 🎯 重点关注bhv参数
                                    if (key.toString().toLowerCase().indexOf('bhv') !== -1 ||
                                        key.toString().toLowerCase().indexOf('behavior') !== -1) {
                                        console.log("\n🔑 ⭐️ 找到bhv参数！");
                                        console.log("🔑 完整内容:", value);
                                        console.log("🔑 长度:", value.length());
                                    }
                                }
                            }

                            console.log("=".repeat(60) + "\n");
                        },
                        onLeave: function(retval) {
                            if (retval) {
                                console.log("✓ 返回值:", new ObjC.Object(retval));
                            }
                        }
                    }
                );

                console.log("✅ Hook成功！");
            }

            // Hook handleCaptchaResult:
            if (UPWSliderCaptchaView['- handleCaptchaResult:']) {
                console.log("[+] 🔗 Hook handleCaptchaResult: ...");

                Interceptor.attach(
                    UPWSliderCaptchaView['- handleCaptchaResult:'].implementation,
                    {
                        onEnter: function(args) {
                            console.log("\n📥 [handleCaptchaResult] 收到验证结果");
                            var result = new ObjC.Object(args[2]);
                            console.log("结果类型:", result.$className);
                            console.log("结果内容:", result.toString());
                        }
                    }
                );

                console.log("✅ Hook成功！");
            }
        } else {
            console.log("[-] ❌ 未找到 UPWSliderCaptchaView 类");
        }
    } catch (e) {
        console.log("[-] ❌ Hook失败:", e);
    }


    // ================================================
    // 第三步：Hook所有网络请求
    // ================================================
    console.log("\n[3] 🌐 Hook网络请求...\n");

    // Hook NSURLSession
    try {
        var NSURLSession = ObjC.classes.NSURLSession;

        if (NSURLSession) {
            console.log("[+] Hook NSURLSession");

            // Hook dataTaskWithRequest:completionHandler:
            var dataTask = NSURLSession['- dataTaskWithRequest:completionHandler:'];
            if (dataTask) {
                Interceptor.attach(dataTask.implementation, {
                    onEnter: function(args) {
                        var request = new ObjC.Object(args[2]);
                        var url = request.URL().toString();

                        // 只关注验证码相关的请求
                        if (url.indexOf('captcha') !== -1 ||
                            url.indexOf('verify') !== -1 ||
                            url.indexOf('vfy') !== -1 ||
                            url.indexOf('slider') !== -1 ||
                            url.indexOf('/session/') !== -1 ||
                            url.indexOf('coupon') !== -1) {

                            console.log("\n🌐 [网络请求]");
                            console.log("URL:", url);
                            console.log("Method:", request.HTTPMethod());

                            var headers = request.allHTTPHeaderFields();
                            if (headers) {
                                console.log("Headers:", headers);
                            }

                            var body = request.HTTPBody();
                            if (body) {
                                console.log("Body:", ObjC.classes.NSString.alloc().initWithData_encoding_(body, 4));
                            }
                        }
                    }
                });
            }
        }
    } catch (e) {
        console.log("[-] Hook网络请求失败:", e);
    }


    // ================================================
    // 第四步：Hook WebView (如果验证码在WebView中)
    // ================================================
    console.log("\n[4] 📱 Hook WebView JS执行...\n");

    try {
        var WKWebView = ObjC.classes.WKWebView;

        if (WKWebView) {
            console.log("[+] Hook WKWebView");

            // Hook evaluateJavaScript:completionHandler:
            var evalJS = WKWebView['- evaluateJavaScript:completionHandler:'];
            if (evalJS) {
                Interceptor.attach(evalJS.implementation, {
                    onEnter: function(args) {
                        var js = new ObjC.Object(args[2]).toString();

                        // 只关注验证码相关的JS
                        if (js.indexOf('captcha') !== -1 ||
                            js.indexOf('verify') !== -1 ||
                            js.indexOf('slider') !== -1 ||
                            js.indexOf('bhv') !== -1) {

                            console.log("\n📜 [WebView执行JS]");
                            console.log(js.substring(0, 500));  // 显示前500字符
                            console.log("...");
                        }
                    }
                });
            }
        }
    } catch (e) {
        console.log("[-] Hook WebView失败:", e);
    }


    console.log("\n[*] ========================================");
    console.log("[*] ✅ 所有Hook已设置完成");
    console.log("[*] 现在请操作APP触发验证码，观察输出");
    console.log("[*] ========================================\n");

} else {
    console.log("[!] Objective-C Runtime不可用");
}
