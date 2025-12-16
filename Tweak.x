// UnionPay Auto Tweak - Network Intercept Version
// Hook all network requests to find and extract bhv parameter

#import <UIKit/UIKit.h>
#import <Foundation/Foundation.h>

static NSString *serverURL = @"http://10.168.0.39:8888/bhv";

// Send bhv to server
static void sendBHVToServer(NSString *bhv) {
    if (!bhv || bhv.length == 0) {
        return;
    }

    NSLog(@"[Tweak] Sending bhv to server: %@", serverURL);

    NSDictionary *jsonData = @{
        @"bhv": bhv,
        @"timestamp": @([[NSDate date] timeIntervalSince1970]),
        @"device": @"iPhone"
    };

    NSError *error = nil;
    NSData *postData = [NSJSONSerialization dataWithJSONObject:jsonData options:0 error:&error];

    if (error) return;

    NSURL *url = [NSURL URLWithString:serverURL];
    NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:url];
    [request setHTTPMethod:@"POST"];
    [request setValue:@"application/json" forHTTPHeaderField:@"Content-Type"];
    [request setHTTPBody:postData];
    [request setTimeoutInterval:5.0];

    NSURLSessionDataTask *task = [[NSURLSession sharedSession] dataTaskWithRequest:request completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
        if (!error) {
            NSLog(@"[Tweak] bhv sent successfully");
        }
    }];

    [task resume];
}

// Extract bhv from dictionary recursively
static void extractBHVFromDict(NSDictionary *dict, NSString *prefix) {
    for (NSString *key in dict.allKeys) {
        id value = dict[key];

        // Check if key contains "bhv" or "behavior"
        if ([key.lowercaseString containsString:@"bhv"] ||
            [key.lowercaseString containsString:@"behavior"]) {

            NSString *bhvValue = [value description];
            NSLog(@"[Tweak] *** FOUND BHV! Key: %@, Value: %@", key, bhvValue);

            // Send to server
            sendBHVToServer(bhvValue);
        }

        // Recursive search in nested dictionaries
        if ([value isKindOfClass:[NSDictionary class]]) {
            extractBHVFromDict((NSDictionary *)value, [NSString stringWithFormat:@"%@.%@", prefix, key]);
        }
        else if ([value isKindOfClass:[NSArray class]]) {
            NSArray *array = (NSArray *)value;
            for (id item in array) {
                if ([item isKindOfClass:[NSDictionary class]]) {
                    extractBHVFromDict((NSDictionary *)item, [NSString stringWithFormat:@"%@.%@[]", prefix, key]);
                }
            }
        }
    }
}

// Hook NSURLSession dataTask methods
%hook NSURLSession

- (NSURLSessionDataTask *)dataTaskWithRequest:(NSURLRequest *)request completionHandler:(void (^)(NSData *, NSURLResponse *, NSError *))completionHandler {

    NSString *url = request.URL.absoluteString;

    // Check if URL contains captcha or verify keywords
    if ([url containsString:@"captcha"] || [url containsString:@"verify"] || [url containsString:@"vfy"]) {

        NSLog(@"[Tweak] Intercepted URL: %@", url);

        // Log request body if exists
        if (request.HTTPBody) {
            NSString *bodyStr = [[NSString alloc] initWithData:request.HTTPBody encoding:NSUTF8StringEncoding];
            NSLog(@"[Tweak] Request body: %@", bodyStr);

            // Try to parse as JSON and extract bhv
            NSError *error = nil;
            id json = [NSJSONSerialization JSONObjectWithData:request.HTTPBody options:0 error:&error];
            if (!error && [json isKindOfClass:[NSDictionary class]]) {
                extractBHVFromDict((NSDictionary *)json, @"request");
            }
        }

        // Wrap completion handler to intercept response
        void (^newHandler)(NSData *, NSURLResponse *, NSError *) = ^(NSData *data, NSURLResponse *response, NSError *error) {

            if (data) {
                NSString *responseStr = [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
                NSLog(@"[Tweak] Response: %@", responseStr);

                // Try to parse response as JSON and extract bhv
                NSError *jsonError = nil;
                id json = [NSJSONSerialization JSONObjectWithData:data options:0 error:&jsonError];
                if (!jsonError && [json isKindOfClass:[NSDictionary class]]) {
                    extractBHVFromDict((NSDictionary *)json, @"response");
                }
            }

            // Call original handler
            completionHandler(data, response, error);
        };

        return %orig(request, newHandler);
    }

    return %orig;
}

- (NSURLSessionDataTask *)dataTaskWithURL:(NSURL *)url completionHandler:(void (^)(NSData *, NSURLResponse *, NSError *))completionHandler {

    NSString *urlStr = url.absoluteString;

    if ([urlStr containsString:@"captcha"] || [urlStr containsString:@"verify"] || [urlStr containsString:@"vfy"]) {
        NSLog(@"[Tweak] Intercepted URL (dataTaskWithURL): %@", urlStr);

        void (^newHandler)(NSData *, NSURLResponse *, NSError *) = ^(NSData *data, NSURLResponse *response, NSError *error) {

            if (data) {
                NSError *jsonError = nil;
                id json = [NSJSONSerialization JSONObjectWithData:data options:0 error:&jsonError];
                if (!jsonError && [json isKindOfClass:[NSDictionary class]]) {
                    extractBHVFromDict((NSDictionary *)json, @"response");
                }
            }

            completionHandler(data, response, error);
        };

        return %orig(url, newHandler);
    }

    return %orig;
}

%end

// Hook NSURLConnection for older APIs
%hook NSURLConnection

+ (NSData *)sendSynchronousRequest:(NSURLRequest *)request returningResponse:(NSURLResponse **)response error:(NSError **)error {

    NSString *url = request.URL.absoluteString;

    if ([url containsString:@"captcha"] || [url containsString:@"verify"] || [url containsString:@"vfy"]) {
        NSLog(@"[Tweak] Intercepted sync request: %@", url);

        if (request.HTTPBody) {
            NSError *jsonError = nil;
            id json = [NSJSONSerialization JSONObjectWithData:request.HTTPBody options:0 error:&jsonError];
            if (!jsonError && [json isKindOfClass:[NSDictionary class]]) {
                extractBHVFromDict((NSDictionary *)json, @"sync_request");
            }
        }
    }

    NSData *data = %orig;

    if (data && ([url containsString:@"captcha"] || [url containsString:@"verify"] || [url containsString:@"vfy"])) {
        NSError *jsonError = nil;
        id json = [NSJSONSerialization JSONObjectWithData:data options:0 error:&jsonError];
        if (!jsonError && [json isKindOfClass:[NSDictionary class]]) {
            extractBHVFromDict((NSDictionary *)json, @"sync_response");
        }
    }

    return data;
}

%end

%ctor {
    NSLog(@"========================================");
    NSLog(@"[Tweak] UnionPay Auto Tweak LOADED");
    NSLog(@"[Tweak] Version: Network-Intercept-1.0");
    NSLog(@"[Tweak] Server: %@", serverURL);
    NSLog(@"[Tweak] Hooking all network requests");
    NSLog(@"========================================");
}
