# Stock Strategy Project
# A股+美股量化策略推荐系统
# 6层架构: 数据层 -> 因子层 -> 策略层 -> 用户画像层 -> 推荐引擎层 -> 输出层

from .data.data_loader import DataLoader
from .factors.factor_engine import FactorEngine
from .strategies.strategy_pool import StrategyPool
from .user_profile.profile_manager import ProfileManager
from .recommendation.recommender import RecommendationEngine
from .output.visualization import Visualizer

__version__ = "1.0.0"
__all__ = [
    "DataLoader",
    "FactorEngine",
    "StrategyPool",
    "ProfileManager",
    "RecommendationEngine",
    "Visualizer"
]
