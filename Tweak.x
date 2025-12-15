// UnionPay Auto Tweak - BHV Capture
// Simplified version without emoji to avoid encoding issues

#import <UIKit/UIKit.h>
#import <Foundation/Foundation.h>

// ========================================
// Interface Declarations
// ========================================

@interface UPWSliderCaptchaView : UIView
- (void)verifySliderCaptcha:(id)param;
- (void)handleCaptchaResult:(id)result;
- (UIImage *)getCaptchaImage;
@end

@interface UPCaptchaSmsModule : NSObject
@end


// ========================================
// Configuration
// ========================================

static BOOL enableAutoClick = YES;
static BOOL enableCaptchaLogging = YES;
static NSString *serverURL = @"http://10.168.0.39:8888/bhv";


// ========================================
// Network Communication
// ========================================

static void sendBHVToServer(NSString *bhv) {
    if (!bhv || bhv.length == 0) {
        NSLog(@"[Tweak] bhv is empty, skipping");
        return;
    }

    NSLog(@"[Tweak] Sending bhv to server: %@", serverURL);

    // Create JSON data
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
        NSLog(@"[Tweak] JSON serialization failed: %@", error.localizedDescription);
        return;
    }

    // Create request
    NSURL *url = [NSURL URLWithString:serverURL];
    NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:url];
    [request setHTTPMethod:@"POST"];
    [request setValue:@"application/json" forHTTPHeaderField:@"Content-Type"];
    [request setHTTPBody:postData];
    [request setTimeoutInterval:5.0];

    // Send request
    NSURLSessionDataTask *task = [[NSURLSession sharedSession]
        dataTaskWithRequest:request
          completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
              if (error) {
                  NSLog(@"[Tweak] Send failed: %@", error.localizedDescription);
                  return;
              }

              NSHTTPURLResponse *httpResponse = (NSHTTPURLResponse *)response;
              NSLog(@"[Tweak] bhv sent successfully, status code: %ld", (long)httpResponse.statusCode);

              if (data) {
                  NSString *responseStr = [[NSString alloc] initWithData:data
                                                                encoding:NSUTF8StringEncoding];
                  NSLog(@"[Tweak] Server response: %@", responseStr);
              }
          }];

    [task resume];
}


// ========================================
// Hook: Captcha View
// ========================================

%hook UPWSliderCaptchaView

- (void)verifySliderCaptcha:(id)param {
    NSLog(@"========================================");
    NSLog(@"[Tweak] verifySliderCaptcha called");
    NSLog(@"========================================");

    if (enableCaptchaLogging) {
        NSLog(@"[Tweak] Parameter type: %@", [param class]);
        NSLog(@"[Tweak] Parameter content: %@", param);

        if ([param isKindOfClass:[NSDictionary class]]) {
            NSDictionary *dict = (NSDictionary *)param;

            for (NSString *key in dict.allKeys) {
                id value = dict[key];
                NSLog(@"  %@ = %@", key, value);

                // Look for bhv parameter
                if ([key.lowercaseString containsString:@"bhv"] ||
                    [key.lowercaseString containsString:@"behavior"]) {
                    NSLog(@"[Tweak] *** Found bhv! ***");
                    NSLog(@"[Tweak] Complete bhv: %@", value);

                    // Send to server
                    NSString *bhvString = [value description];
                    sendBHVToServer(bhvString);

                    // Also post notification
                    [[NSNotificationCenter defaultCenter]
                        postNotificationName:@"BHVCaptured"
                                      object:value];
                }
            }
        }
    }

    // Call original method
    %orig;

    NSLog(@"[Tweak] Original method executed");
    NSLog(@"========================================\n");
}

- (void)handleCaptchaResult:(id)result {
    NSLog(@"[Tweak] Received captcha result");
    NSLog(@"Result: %@", result);

    %orig;

    if ([result isKindOfClass:[NSDictionary class]]) {
        NSDictionary *dict = (NSDictionary *)result;
        NSString *code = dict[@"resCode"];

        if ([code isEqualToString:@"0000"]) {
            NSLog(@"[Tweak] Captcha verification successful!");

            [[NSNotificationCenter defaultCenter]
                postNotificationName:@"CaptchaSuccess"
                              object:nil];
        } else {
            NSLog(@"[Tweak] Captcha verification failed: %@", dict[@"resMsg"]);
        }
    }
}

- (UIImage *)getCaptchaImage {
    UIImage *image = %orig;

    if (image && enableCaptchaLogging) {
        NSLog(@"[Tweak] Got captcha image");
        NSLog(@"Image size: %.0fx%.0f", image.size.width, image.size.height);
    }

    return image;
}

%end


// ========================================
// Hook: Network Requests (Monitor API)
// ========================================

%hook NSURLSession

- (NSURLSessionDataTask *)dataTaskWithRequest:(NSURLRequest *)request
                             completionHandler:(void (^)(NSData *, NSURLResponse *, NSError *))completionHandler {

    NSString *url = request.URL.absoluteString;

    // Monitor key APIs
    if ([url containsString:@"captcha"] ||
        [url containsString:@"verify"] ||
        [url containsString:@"coupon"] ||
        [url containsString:@"/session/"] ||
        [url containsString:@"acquire"]) {

        NSLog(@"\n[Network Request]");
        NSLog(@"URL: %@", url);
        NSLog(@"Method: %@", request.HTTPMethod);

        // Wrap completion handler to log response
        void (^newHandler)(NSData *, NSURLResponse *, NSError *) =
            ^(NSData *data, NSURLResponse *response, NSError *error) {

            if (data) {
                NSString *responseStr = [[NSString alloc] initWithData:data
                                                              encoding:NSUTF8StringEncoding];
                NSLog(@"[Response]: %@", responseStr);
            }

            if (error) {
                NSLog(@"[Error]: %@", error.localizedDescription);
            }

            // Call original handler
            completionHandler(data, response, error);
        };

        return %orig(request, newHandler);
    }

    return %orig;
}

%end


// ========================================
// Constructor (executed when Tweak loads)
// ========================================

%ctor {
    NSLog(@"\n");
    NSLog(@"========================================");
    NSLog(@"UnionPay Auto Tweak Loaded");
    NSLog(@"Version: 1.0.0");
    NSLog(@"Server: %@", serverURL);
    NSLog(@"========================================");
    NSLog(@"\n");

    // Listen for notifications
    [[NSNotificationCenter defaultCenter]
        addObserverForName:@"BHVCaptured"
                    object:nil
                     queue:nil
                usingBlock:^(NSNotification *notification) {
                    NSString *bhv = notification.object;
                    NSLog(@"[Notification] Captured bhv: %@", bhv);
                }];

    [[NSNotificationCenter defaultCenter]
        addObserverForName:@"CaptchaSuccess"
                    object:nil
                     queue:nil
                usingBlock:^(NSNotification *notification) {
                    NSLog(@"[Notification] Captcha verification successful");
                }];
}
