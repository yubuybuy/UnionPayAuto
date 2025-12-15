// ========================================
// 云闪付完整类导出工具 - Frida脚本
// ========================================
//
// 功能：导出所有类、方法、属性到JSON文件
// 用法：frida -U -n 云闪付 -l frida_class_dump.js
//
// ========================================

console.log("[*] 开始导出云闪付类信息...\n");

if (ObjC.available) {

    var classInfo = {
        "timestamp": new Date().toISOString(),
        "device": "iPhone",
        "app": "云闪付",
        "classes": {}
    };

    var relevantClasses = [];
    var allClasses = Object.keys(ObjC.classes);

    console.log("[*] 总类数量:", allClasses.length);
    console.log("[*] 筛选相关类...\n");

    // 筛选相关的类
    var keywords = [
        'captcha', 'Captcha',
        'slider', 'Slider',
        'verify', 'Verify',
        'coupon', 'Coupon',
        'acquire', 'Acquire',
        'UPW',  // 云闪付前缀
        'UP',   // 银联前缀
    ];

    allClasses.forEach(function(className) {
        for (var i = 0; i < keywords.length; i++) {
            if (className.indexOf(keywords[i]) !== -1) {
                relevantClasses.push(className);
                break;
            }
        }
    });

    console.log("[+] 找到", relevantClasses.length, "个相关类\n");

    // 导出每个类的详细信息
    relevantClasses.forEach(function(className) {
        try {
            var clazz = ObjC.classes[className];

            console.log("[+] 处理:", className);

            var classData = {
                "name": className,
                "superclass": null,
                "protocols": [],
                "instanceMethods": [],
                "classMethods": [],
                "properties": [],
                "ivars": []
            };

            // 父类
            try {
                if (clazz.$superClass) {
                    classData.superclass = clazz.$superClass.$className;
                }
            } catch (e) {}

            // 实例方法
            try {
                var methods = clazz.$ownMethods;
                methods.forEach(function(method) {
                    if (method.startsWith('- ')) {
                        classData.instanceMethods.push(method.substring(2));
                    } else if (method.startsWith('+ ')) {
                        classData.classMethods.push(method.substring(2));
                    }
                });
            } catch (e) {
                console.log("  [-] 获取方法失败:", e.message);
            }

            // 属性
            try {
                var props = clazz.$ownProperties;
                if (props) {
                    props.forEach(function(prop) {
                        classData.properties.push(prop);
                    });
                }
            } catch (e) {}

            classInfo.classes[className] = classData;

        } catch (e) {
            console.log("  [-] 处理失败:", e.message);
        }
    });

    // 输出JSON
    var output = JSON.stringify(classInfo, null, 2);

    console.log("\n" + "=".repeat(60));
    console.log("导出完成！");
    console.log("=".repeat(60));
    console.log("\n导出的类数量:", Object.keys(classInfo.classes).length);

    // 保存到文件（需要通过RPC调用）
    console.log("\n--- JSON输出开始 ---");
    console.log(output);
    console.log("--- JSON输出结束 ---\n");

    // 统计信息
    console.log("\n=== 统计信息 ===");

    var captchaClasses = [];
    var couponClasses = [];
    var verifyClasses = [];

    for (var name in classInfo.classes) {
        if (name.toLowerCase().indexOf('captcha') !== -1) {
            captchaClasses.push(name);
        }
        if (name.toLowerCase().indexOf('coupon') !== -1) {
            couponClasses.push(name);
        }
        if (name.toLowerCase().indexOf('verify') !== -1) {
            verifyClasses.push(name);
        }
    }

    console.log("\n验证码相关类 (" + captchaClasses.length + "):");
    captchaClasses.forEach(function(n) { console.log("  - " + n); });

    console.log("\n优惠券相关类 (" + couponClasses.length + "):");
    couponClasses.forEach(function(n) { console.log("  - " + n); });

    console.log("\n验证相关类 (" + verifyClasses.length + "):");
    verifyClasses.forEach(function(n) { console.log("  - " + n); });

    console.log("\n=== 重点关注的类和方法 ===\n");

    // UPWSliderCaptchaView 详细信息
    if (classInfo.classes['UPWSliderCaptchaView']) {
        console.log("📱 UPWSliderCaptchaView:");
        var methods = classInfo.classes['UPWSliderCaptchaView'].instanceMethods;
        methods.forEach(function(m) {
            console.log("    " + m);
        });
    }

} else {
    console.log("[!] Objective-C Runtime 不可用");
}

// RPC导出函数
rpc.exports = {
    dumpClasses: function() {
        return classInfo;
    },

    getClassInfo: function(className) {
        if (ObjC.classes[className]) {
            var clazz = ObjC.classes[className];
            return {
                methods: clazz.$ownMethods,
                properties: clazz.$ownProperties || []
            };
        }
        return null;
    }
};

console.log("\n[*] 可以通过RPC调用 dumpClasses() 获取数据");
