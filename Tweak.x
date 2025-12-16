// UnionPay Auto Tweak - Aggressive All-Network Hook
// Hooks EVERYTHING to find what network library UnionPay uses

#import <UIKit/UIKit.h>
#import <Foundation/Foundation.h>
#import <WebKit/WebKit.h>

static int requestCount = 0;

// Hook ALL NSURLSession methods
%hook NSURLSession

- (NSURLSessionDataTask *)dataTaskWithRequest:(NSURLRequest *)request completionHandler:(void (^)(NSData *, NSURLResponse *, NSError *))completionHandler {
    requestCount++;
    NSLog(@"[Tweak-%d] NSURLSession.dataTaskWithRequest: %@", requestCount, request.URL.absoluteString);
    return %orig;
}

- (NSURLSessionDataTask *)dataTaskWithURL:(NSURL *)url completionHandler:(void (^)(NSData *, NSURLResponse *, NSError *))completionHandler {
    requestCount++;
    NSLog(@"[Tweak-%d] NSURLSession.dataTaskWithURL: %@", requestCount, url.absoluteString);
    return %orig;
}

- (NSURLSessionUploadTask *)uploadTaskWithRequest:(NSURLRequest *)request fromData:(NSData *)bodyData completionHandler:(void (^)(NSData *, NSURLResponse *, NSError *))completionHandler {
    requestCount++;
    NSLog(@"[Tweak-%d] NSURLSession.uploadTask: %@", requestCount, request.URL.absoluteString);
    return %orig;
}

%end

// Hook NSURLConnection
%hook NSURLConnection

+ (NSData *)sendSynchronousRequest:(NSURLRequest *)request returningResponse:(NSURLResponse **)response error:(NSError **)error {
    requestCount++;
    NSLog(@"[Tweak-%d] NSURLConnection.sendSynchronous: %@", requestCount, request.URL.absoluteString);
    return %orig;
}

- (id)initWithRequest:(NSURLRequest *)request delegate:(id)delegate {
    requestCount++;
    NSLog(@"[Tweak-%d] NSURLConnection.init: %@", requestCount, request.URL.absoluteString);
    return %orig;
}

%end

// Hook CFNetwork level (lower level)
%hook NSMutableURLRequest

- (id)initWithURL:(NSURL *)url {
    requestCount++;
    NSLog(@"[Tweak-%d] NSMutableURLRequest.init: %@", requestCount, url.absoluteString);
    return %orig;
}

%end

%hook NSURLRequest

- (id)initWithURL:(NSURL *)url {
    requestCount++;
    NSLog(@"[Tweak-%d] NSURLRequest.init: %@", requestCount, url.absoluteString);
    return %orig;
}

%end

// Hook all UIWebView methods
%hook UIWebView

- (void)loadRequest:(NSURLRequest *)request {
    requestCount++;
    NSLog(@"[Tweak-%d] UIWebView.loadRequest: %@", requestCount, request.URL.absoluteString);
    %orig;
}

%end

// Hook WKWebView
%hook WKWebView

- (WKNavigation *)loadRequest:(NSURLRequest *)request {
    requestCount++;
    NSLog(@"[Tweak-%d] WKWebView.loadRequest: %@", requestCount, request.URL.absoluteString);
    return %orig;
}

%end

// Constructor
%ctor {
    NSLog(@"========================================");
    NSLog(@"[Tweak] AGGRESSIVE NETWORK HOOK LOADED");
    NSLog(@"[Tweak] Version: All-Network-1.0");
    NSLog(@"[Tweak] Hooks: ALL network methods");
    NSLog(@"========================================");
}
