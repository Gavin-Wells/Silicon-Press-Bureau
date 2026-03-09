class MailError(Exception):
    """邮件模块基础异常。"""


class MailConfigurationError(MailError):
    """邮件配置不完整或非法。"""


class MailDeliveryError(MailError):
    """邮件发送失败。"""
