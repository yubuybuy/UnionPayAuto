// UnionPay Auto Tweak - TEST VERSION
// This is a minimal test version that only shows an alert when the app starts
// Used to verify TrollFools injection is working

#import <UIKit/UIKit.h>
#import <Foundation/Foundation.h>

// Test function to show alert
static void showTestAlert() {
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(2 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        UIAlertController *alert = [UIAlertController
            alertControllerWithTitle:@"Tweak Test"
            message:@"UnionPay Auto Tweak is LOADED!\n\nIf you see this, TrollFools injection is working!"
            preferredStyle:UIAlertControllerStyleAlert];

        [alert addAction:[UIAlertAction
            actionWithTitle:@"OK"
            style:UIAlertActionStyleDefault
            handler:nil]];

        UIWindow *window = [[UIApplication sharedApplication] keyWindow];
        UIViewController *rootVC = window.rootViewController;

        if (rootVC) {
            [rootVC presentViewController:alert animated:YES completion:nil];
        }
    });
}

// Constructor - runs when tweak loads
%ctor {
    NSLog(@"========================================");
    NSLog(@"[TEST] UnionPay Auto Tweak LOADED");
    NSLog(@"[TEST] Version: TEST-1.0");
    NSLog(@"[TEST] This is a test version");
    NSLog(@"========================================");

    // Show alert after 2 seconds
    showTestAlert();
}
