// ========================================
// 云闪付自动化 - Tweak Hook代码
// ========================================
//
// 编译方法:
// 1. 安装Theos: https://theos.dev
// 2. 创建项目: $THEOS/bin/nic.pl (选择 iphone/tweak)
// 3. 将本文件内容替换 Tweak.x
// 4. make package
// 5. 通过TrollFools安装生成�?deb
//
// ========================================

#import <UIKit/UIKit.h>
#import <Foundation/Foundation.h>

// ========================================
// 接口声明（从IPA分析得出�?
// ========================================

@interface UPWSliderCaptchaView : UIView
- (void)verifySliderCaptcha:(id)param;
- (void)handleCaptchaResult:(id)result;
- (UIImage *)getCaptchaImage;
@end

@interface UPCaptchaSmsModule : NSObject
@end

// 假设的优惠券控制器（需要通过Frida确认实际类名�?
@interface UPCouponViewController : UIViewController
@property (nonatomic, strong) UIButton *acquireButton;
- (void)onAcquireButtonTapped:(UIButton *)sender;
@end


// ========================================
// 配置参数
// ========================================

static BOOL enableAutoClick = YES;        // 是否自动点击领券按钮
static BOOL enableCaptchaLogging = YES;   // 是否记录验证码日�?
static CGFloat manualDistance = 0;        // 手动输入的验证码距离
static NSString *serverURL = @"http://10.168.0.39:8888/bhv";  // Python服务器地址

// ========================================
// 网络通信功能
// ========================================

void sendBHVToServer(NSString *bhv) {
    if (!bhv || bhv.length == 0) {
        NSLog(@"⚠️ [Tweak] bhv为空，跳过发�?);
        return;
    }

    NSLog(@"📡 [Tweak] 准备发送bhv到服务器: %@", serverURL);

    // 构造JSON数据
    NSDictionary *jsonData = @{
        @"bhv": bhv,
        @"timestamp": @([[NSDate date] timeIntervalSince1970]),
        @"device": @"iPhone"
    };

    NSError *error = nil;
    NSData *postData = [NSJSONSerialization dataWithJSONObject:jsonData
                                                       options:0
                                                         error:&error];

    if (error) {
        NSLog(@"�?[Tweak] JSON序列化失�? %@", error.localizedDescription);
        return;
    }

    // 创建请求
    NSURL *url = [NSURL URLWithString:serverURL];
    NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:url];
    [request setHTTPMethod:@"POST"];
    [request setValue:@"application/json" forHTTPHeaderField:@"Content-Type"];
    [request setHTTPBody:postData];
    [request setTimeoutInterval:5.0];

    // 发送请�?
    NSURLSessionDataTask *task = [[NSURLSession sharedSession]
        dataTaskWithRequest:request
          completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
              if (error) {
                  NSLog(@"�?[Tweak] 发送失�? %@", error.localizedDescription);
                  return;
              }

              NSHTTPURLResponse *httpResponse = (NSHTTPURLResponse *)response;
              NSLog(@"�?[Tweak] bhv发送成功，状态码: %ld", (long)httpResponse.statusCode);

              if (data) {
                  NSString *responseStr = [[NSString alloc] initWithData:data
                                                                encoding:NSUTF8StringEncoding];
                  NSLog(@"📥 [Tweak] 服务器响�? %@", responseStr);
              }
          }];

    [task resume];
}


// ========================================
// Hook 1: 验证码视�?
// ========================================

%hook UPWSliderCaptchaView

// 核心方法：验证滑动验证码
- (void)verifySliderCaptcha:(id)param {
    NSLog(@"========================================");
    NSLog(@"🎯 [Tweak] verifySliderCaptcha 被调�?);
    NSLog(@"========================================");

    if (enableCaptchaLogging) {
        NSLog(@"📋 参数类型: %@", [param class]);
        NSLog(@"📋 参数内容: %@", param);

        // 如果是字典，遍历所有键值对
        if ([param isKindOfClass:[NSDictionary class]]) {
            NSDictionary *dict = (NSDictionary *)param;

            for (NSString *key in dict.allKeys) {
                id value = dict[key];
                NSLog(@"  %@ = %@", key, value);

                // 🔑 重点关注bhv参数
                if ([key.lowercaseString containsString:@"bhv"] ||
                    [key.lowercaseString containsString:@"behavior"]) {
                    NSLog(@"🔑 ⭐️ 找到bhv�?);
                    NSLog(@"🔑 完整bhv: %@", value);

                    // 发送到服务�?
                    NSString *bhvString = [value description];
                    sendBHVToServer(bhvString);

                    // 同时发送通知
                    [[NSNotificationCenter defaultCenter]
                        postNotificationName:@"BHVCaptured"
                                      object:value];
                }
            }
        }
    }

    // 调用原方法，让验证正常进�?
    %orig;

    NSLog(@"�?[Tweak] 原方法执行完�?);
    NSLog(@"========================================\n");
}

// Hook 验证码结果处�?
- (void)handleCaptchaResult:(id)result {
    NSLog(@"📥 [Tweak] 收到验证码结�?);
    NSLog(@"结果: %@", result);

    %orig;

    // 可以在这里判断是否成功，并采取后续行�?
    if ([result isKindOfClass:[NSDictionary class]]) {
        NSDictionary *dict = (NSDictionary *)result;
        NSString *code = dict[@"resCode"];

        if ([code isEqualToString:@"0000"]) {
            NSLog(@"�?验证码验证成功！");

            // 可以触发自动领券
            [[NSNotificationCenter defaultCenter]
                postNotificationName:@"CaptchaSuccess"
                              object:nil];
        } else {
            NSLog(@"�?验证码验证失�? %@", dict[@"resMsg"]);
        }
    }
}

// Hook 获取验证码图片（可以用于OCR识别�?
- (UIImage *)getCaptchaImage {
    UIImage *image = %orig;

    if (image && enableCaptchaLogging) {
        NSLog(@"🖼�?[Tweak] 获取到验证码图片");
        NSLog(@"图片尺寸: %.0fx%.0f", image.size.width, image.size.height);

        // 可以保存图片用于OCR识别
        // [self saveCaptchaImage:image];
    }

    return image;
}

// 新增方法：手动输入验证码距离
%new
- (void)showDistanceInputAlert {
    UIAlertController *alert = [UIAlertController
        alertControllerWithTitle:@"验证�?
                         message:@"请输入滑动距�?px)"
                  preferredStyle:UIAlertControllerStyleAlert];

    [alert addTextFieldWithConfigurationHandler:^(UITextField *textField) {
        textField.placeholder = @"150";
        textField.keyboardType = UIKeyboardTypeDecimalPad;
    }];

    [alert addAction:[UIAlertAction
        actionWithTitle:@"确定"
                  style:UIAlertActionStyleDefault
                handler:^(UIAlertAction *action) {
                    NSString *input = alert.textFields.firstObject.text;
                    CGFloat distance = input.floatValue;

                    NSLog(@"👤 [Tweak] 用户输入距离: %.2f", distance);

                    // 这里需要构造参数调用验证方�?
                    // 参数格式需要通过Frida观察确定
                    NSDictionary *params = @{
                        @"distance": @(distance),
                        @"time": @(1500),  // 模拟1.5秒完�?
                        // @"bhv": ...,  // 这个由原方法生成
                    };

                    [self verifySliderCaptcha:params];
                }]];

    [alert addAction:[UIAlertAction
        actionWithTitle:@"取消"
                  style:UIAlertActionStyleCancel
                handler:nil]];

    // 显示Alert
    UIViewController *rootVC = [UIApplication sharedApplication].keyWindow.rootViewController;
    [rootVC presentViewController:alert animated:YES completion:nil];
}

%end


// ========================================
// Hook 2: 优惠券页面（示例，需要确认实际类名）
// ========================================

/*
// 取消注释并修改为实际的类�?

%hook UPCouponViewController

// 页面加载完成后自动执�?
- (void)viewDidAppear:(BOOL)animated {
    %orig;

    if (enableAutoClick) {
        NSLog(@"🚀 [Tweak] 优惠券页面加载完�?);

        // 延迟2秒后自动点击（等待界面稳定）
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(2 * NSEC_PER_SEC)),
                       dispatch_get_main_queue(), ^{
            [self autoClickAcquireButton];
        });
    }
}

%new
- (void)autoClickAcquireButton {
    NSLog(@"🤖 [Tweak] 自动点击领券按钮");

    UIButton *button = self.acquireButton;

    if (button && button.enabled) {
        // 方案A: 触发真实的UI事件（推荐）
        [button sendActionsForControlEvents:UIControlEventTouchUpInside];
        NSLog(@"�?已触发按钮点击事�?);
    } else if (button) {
        NSLog(@"⚠️ 按钮存在但被禁用");
    } else {
        NSLog(@"�?未找到领券按�?);

        // 尝试查找按钮
        [self findAndClickAcquireButton];
    }
}

%new
- (void)findAndClickAcquireButton {
    NSLog(@"🔍 尝试查找领券按钮...");

    // 遍历所有子视图查找按钮
    [self findButtonInView:self.view];
}

%new
- (void)findButtonInView:(UIView *)view {
    for (UIView *subview in view.subviews) {
        if ([subview isKindOfClass:[UIButton class]]) {
            UIButton *button = (UIButton *)subview;
            NSString *title = button.currentTitle;

            // 查找包含"领取"�?�?等关键词的按�?
            if ([title containsString:@"领取"] ||
                [title containsString:@"�?] ||
                [title containsString:@"立即"]) {

                NSLog(@"�?找到按钮: %@", title);
                [button sendActionsForControlEvents:UIControlEventTouchUpInside];
                return;
            }
        }

        // 递归查找子视�?
        [self findButtonInView:subview];
    }
}

%end
*/


// ========================================
// Hook 3: 网络请求（监控API调用�?
// ========================================

%hook NSURLSession

- (NSURLSessionDataTask *)dataTaskWithRequest:(NSURLRequest *)request
                             completionHandler:(void (^)(NSData *, NSURLResponse *, NSError *))completionHandler {

    NSString *url = request.URL.absoluteString;

    // 监控关键API
    if ([url containsString:@"captcha"] ||
        [url containsString:@"verify"] ||
        [url containsString:@"coupon"] ||
        [url containsString:@"/session/"] ||
        [url containsString:@"acquire"]) {

        NSLog(@"\n🌐 [网络请求]");
        NSLog(@"URL: %@", url);
        NSLog(@"Method: %@", request.HTTPMethod);

        // 修改完成回调，记录响�?
        void (^newHandler)(NSData *, NSURLResponse *, NSError *) =
            ^(NSData *data, NSURLResponse *response, NSError *error) {

            if (data) {
                NSString *responseStr = [[NSString alloc] initWithData:data
                                                              encoding:NSUTF8StringEncoding];
                NSLog(@"📥 响应: %@", responseStr);
            }

            if (error) {
                NSLog(@"�?错误: %@", error.localizedDescription);
            }

            // 调用原回�?
            completionHandler(data, response, error);
        };

        return %orig(request, newHandler);
    }

    return %orig;
}

%end


// ========================================
// 构造函数（Tweak加载时执行）
// ========================================

%ctor {
    NSLog(@"\n");
    NSLog(@"========================================");
    NSLog(@"🚀 云闪付自动化 Tweak 已加�?);
    NSLog(@"版本: 1.0.0");
    NSLog(@"========================================");
    NSLog(@"\n");

    // 监听通知
    [[NSNotificationCenter defaultCenter]
        addObserverForName:@"BHVCaptured"
                    object:nil
                     queue:nil
                usingBlock:^(NSNotification *notification) {
                    NSString *bhv = notification.object;
                    NSLog(@"📮 [通知] 捕获到bhv: %@", bhv);

                    // 可以保存到文件或发送到服务�?
                }];

    [[NSNotificationCenter defaultCenter]
        addObserverForName:@"CaptchaSuccess"
                    object:nil
                     queue:nil
                usingBlock:^(NSNotification *notification) {
                    NSLog(@"📮 [通知] 验证码验证成�?);

                    // 可以触发后续自动化操�?
                }];
}


// ========================================
// 使用说明
// ========================================

/*

编译步骤�?

1. 安装Theos (macOS/Linux):
   bash -c "$(curl -fsSL https://raw.githubusercontent.com/theos/theos/master/bin/install-theos)"

2. 创建项目:
   $THEOS/bin/nic.pl
   - 选择 [1.] iphone/tweak
   - Project Name: UnionPayAuto
   - Package Name: com.yourname.unionpayauto
   - Author: Your Name
   - Bundle filter: com.unionpay.chsp

3. 编辑Makefile:
   TARGET := iphone:clang:latest:14.0
   ARCHS = arm64

   include $(THEOS)/makefiles/common.mk

   TWEAK_NAME = UnionPayAuto

   UnionPayAuto_FILES = Tweak.x
   UnionPayAuto_CFLAGS = -fobjc-arc

   include $(THEOS_MAKE_PATH)/tweak.mk

4. 替换Tweak.x为本文件内容

5. 编译:
   make package

6. 安装:
   - 将生成的.deb传输到手�?
   - 使用TrollFools安装
   - 重启云闪付APP

调试方法�?

1. 查看日志:
   idevicesyslog | grep Tweak

2. 使用Console.app (macOS):
   连接手机，过�?Tweak"关键�?

注意事项�?

1. 确保手机已安装TrollStore
2. 确保TrollFools已配置正�?
3. Hook的类名和方法名需要通过Frida确认
4. 编译前需要修改实际的类名和方法签�?

*/
