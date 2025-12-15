export PREFIX = /usr
TARGET := iphone:clang:latest:11.0
ARCHS = arm64 arm64e

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = UnionPayAuto

UnionPayAuto_FILES = Tweak.x
UnionPayAuto_CFLAGS = -fobjc-arc
UnionPayAuto_FRAMEWORKS = UIKit Foundation

include $(THEOS_MAKE_PATH)/tweak.mk
