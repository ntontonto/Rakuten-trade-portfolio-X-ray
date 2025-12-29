"""
AI Insights Service using Google Gemini

Generates portfolio analysis reports and recommendations

Ported from JavaScript (index.html lines 1135-1168)
"""
from typing import Dict, Optional
import google.generativeai as genai

from app.config import settings


class AIInsightsGenerator:
    """Generates AI-powered portfolio insights using Gemini"""

    def __init__(self):
        """Initialize Gemini AI"""
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None

    def generate_portfolio_report(
        self,
        total_value: float,
        total_xirr: float,
        core_ratio: float,
        top_asset_class: str,
        holdings_count: int
    ) -> Dict[str, str]:
        """
        Generate comprehensive portfolio analysis report

        Args:
            total_value: Total portfolio value in JPY
            total_xirr: Portfolio XIRR (annualized return)
            core_ratio: Percentage of Core (long-term) holdings
            top_asset_class: Largest asset class by value
            holdings_count: Number of holdings

        Returns:
            Dict with 'report' (markdown) and 'status' keys
        """
        if not self.model:
            return {
                'status': 'error',
                'report': 'AI insights unavailable. Please configure GEMINI_API_KEY in environment variables.'
            }

        # Format XIRR as percentage
        xirr_percent = f"{total_xirr * 100:.2f}%"

        # Build prompt (matches original JS prompt)
        prompt = f"""
あなたはプロの投資顧問（IFA）です。以下のポートフォリオデータを分析し、投資家へアドバイスを行ってください。

- 総資産評価額: ¥{total_value:,.0f}
- 全体XIRR (年率): {xirr_percent}
- コア(長期)比率: {core_ratio:.1f}% (目標は80%以上)
- 最大アセットクラス: {top_asset_class}
- 保有銘柄数: {holdings_count}

指示: Markdown形式で、以下の3つのセクションを日本語で記述してください。

1. **健全性診断 (80:20ルール)**
   - コア/サテライト比率の評価
   - 推奨される改善点

2. **パフォーマンス評価**
   - XIRRの妥当性（市場平均との比較）
   - アセットクラス配分の適切性

3. **リバランス提案**
   - 具体的な売買推奨（もしあれば）
   - リスク管理の観点からのアドバイス
"""

        try:
            response = self.model.generate_content(prompt)

            # Check if response has text
            if hasattr(response, 'text') and response.text:
                return {
                    'status': 'success',
                    'report': response.text
                }
            else:
                # Handle safety filter or blocked response
                return {
                    'status': 'error',
                    'report': 'AI生成に失敗しました。コンテンツがフィルタリングされた可能性があります。'
                }

        except Exception as e:
            return {
                'status': 'error',
                'report': f'AI分析の生成中にエラーが発生しました: {str(e)}'
            }

    def generate_holding_analysis(
        self,
        symbol: str,
        name: str,
        xirr: float,
        holding_days: int,
        unrealized_pl: float
    ) -> str:
        """
        Generate analysis for a specific holding

        Args:
            symbol: Security symbol
            name: Security name
            xirr: Holding XIRR
            holding_days: Days held
            unrealized_pl: Unrealized P&L in JPY

        Returns:
            Analysis text
        """
        if not self.model:
            return "AI insights unavailable."

        prompt = f"""
投資銘柄の分析を行ってください。

- 銘柄: {name} ({symbol})
- 保有期間: {holding_days}日
- XIRR: {xirr * 100:.2f}%
- 含み損益: ¥{unrealized_pl:,.0f}

この銘柄について、30文字以内で簡潔なコメントを日本語で提供してください。
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text if hasattr(response, 'text') else "分析に失敗しました"
        except Exception as e:
            return f"エラー: {str(e)}"
