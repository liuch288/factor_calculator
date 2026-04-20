"""
用户需求：
    用户想计算 TL 合约 2026-01-01 到 2026-02-28 的 BiquotePEU，问有哪些入参。

Agent 操作：
    通过 factory 模块动态定位 BiquotePEU 类，用 inspect 查看其 __init__ 签名和文档。

结果：
    BiquotePEU(order_maintaining_time=None, lb=1, la=1)
    - order_maintaining_time (float): 挂单维持时长（秒），仅支持固定时长
    - lb (int, 默认1): 买方挂单档位
    - la (int, 默认1): 卖方挂单档位
"""

import importlib
import inspect
import pkgutil


def inspect_unit_params(class_name: str):
    """动态查找并打印任意 DMU/PEU 类的构造函数签名和文档。"""
    from factor_calculator.factory import get_module_for_class

    mod, path = get_module_for_class(class_name)
    cls = None

    if hasattr(mod, class_name):
        cls = getattr(mod, class_name)
    else:
        if hasattr(mod, "__path__"):
            for importer, subname, ispkg in pkgutil.iter_modules(
                mod.__path__, mod.__name__ + "."
            ):
                try:
                    submod = importlib.import_module(subname)
                    if hasattr(submod, class_name):
                        cls = getattr(submod, class_name)
                        break
                except Exception:
                    pass

    if cls is None:
        print(f"{class_name} not found")
        return

    sig = inspect.signature(cls.__init__)
    print(f"{class_name}.__init__ signature: {sig}")
    doc = cls.__init__.__doc__ or cls.__doc__
    if doc:
        print(f"Docstring:\n{doc}")


if __name__ == "__main__":
    inspect_unit_params("BiquotePEU")
