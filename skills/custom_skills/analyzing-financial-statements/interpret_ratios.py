"""
Financial ratio interpretation module.
Provides industry benchmarks and contextual analysis.
"""

from typing import Any


class RatioInterpreter:
    """Interpret financial ratios with industry context."""

    # Industry benchmark ranges (simplified for demonstration)
    BENCHMARKS = {
        "technology": {
            "current_ratio": {"excellent": 2.5, "good": 1.8, "acceptable": 1.2, "poor": 1.0},
            "debt_to_equity": {"excellent": 0.3, "good": 0.5, "acceptable": 1.0, "poor": 2.0},
            "roe": {"excellent": 0.25, "good": 0.18, "acceptable": 0.12, "poor": 0.08},
            "gross_margin": {"excellent": 0.70, "good": 0.50, "acceptable": 0.35, "poor": 0.20},
            "pe_ratio": {"undervalued": 15, "fair": 25, "growth": 35, "expensive": 50},
        },
        "retail": {
            "current_ratio": {"excellent": 2.0, "good": 1.5, "acceptable": 1.0, "poor": 0.8},
            "debt_to_equity": {"excellent": 0.5, "good": 0.8, "acceptable": 1.5, "poor": 2.5},
            "roe": {"excellent": 0.20, "good": 0.15, "acceptable": 0.10, "poor": 0.05},
            "gross_margin": {"excellent": 0.40, "good": 0.30, "acceptable": 0.20, "poor": 0.10},
            "pe_ratio": {"undervalued": 12, "fair": 18, "growth": 25, "expensive": 35},
        },
        "financial": {
            "current_ratio": {"excellent": 1.5, "good": 1.2, "acceptable": 1.0, "poor": 0.8},
            "debt_to_equity": {"excellent": 1.0, "good": 2.0, "acceptable": 4.0, "poor": 6.0},
            "roe": {"excellent": 0.15, "good": 0.12, "acceptable": 0.08, "poor": 0.05},
            "pe_ratio": {"undervalued": 10, "fair": 15, "growth": 20, "expensive": 30},
        },
        "manufacturing": {
            "current_ratio": {"excellent": 2.2, "good": 1.7, "acceptable": 1.3, "poor": 1.0},
            "debt_to_equity": {"excellent": 0.4, "good": 0.7, "acceptable": 1.2, "poor": 2.0},
            "roe": {"excellent": 0.18, "good": 0.14, "acceptable": 0.10, "poor": 0.06},
            "gross_margin": {"excellent": 0.35, "good": 0.25, "acceptable": 0.18, "poor": 0.12},
            "pe_ratio": {"undervalued": 14, "fair": 20, "growth": 28, "expensive": 40},
        },
        "healthcare": {
            "current_ratio": {"excellent": 2.3, "good": 1.8, "acceptable": 1.4, "poor": 1.0},
            "debt_to_equity": {"excellent": 0.3, "good": 0.6, "acceptable": 1.0, "poor": 1.8},
            "roe": {"excellent": 0.22, "good": 0.16, "acceptable": 0.11, "poor": 0.07},
            "gross_margin": {"excellent": 0.65, "good": 0.45, "acceptable": 0.30, "poor": 0.20},
            "pe_ratio": {"undervalued": 18, "fair": 28, "growth": 40, "expensive": 55},
        },
    }

    def __init__(self, industry: str = "general"):
        """
        Initialize interpreter with industry context.

        Args:
            industry: Industry sector for benchmarking
        """
        self.industry = industry.lower()
        self.benchmarks = self.BENCHMARKS.get(self.industry, self._get_general_benchmarks())

    def _get_general_benchmarks(self) -> dict[str, Any]:
        """Get general industry-agnostic benchmarks."""
        return {
            "current_ratio": {"excellent": 2.0, "good": 1.5, "acceptable": 1.0, "poor": 0.8},
            "debt_to_equity": {"excellent": 0.5, "good": 1.0, "acceptable": 1.5, "poor": 2.5},
            "roe": {"excellent": 0.20, "good": 0.15, "acceptable": 0.10, "poor": 0.05},
            "gross_margin": {"excellent": 0.40, "good": 0.30, "acceptable": 0.20, "poor": 0.10},
            "pe_ratio": {"undervalued": 15, "fair": 22, "growth": 30, "expensive": 45},
        }

    def interpret_ratio(self, ratio_name: str, value: float) -> dict[str, Any]:
        """
        Interpret a single ratio with context.

        Args:
            ratio_name: Name of the ratio
            value: Calculated ratio value

        Returns:
            Dictionary with interpretation details
        """
        interpretation = {
            "value": value,
            "rating": "N/A",
            "message": "",
            "recommendation": "",
            "benchmark_comparison": {},
        }

        if ratio_name in self.benchmarks:
            benchmark = self.benchmarks[ratio_name]
            interpretation["benchmark_comparison"] = benchmark

            # Determine rating based on benchmarks
            if ratio_name in ["current_ratio", "roe", "gross_margin"]:
                # Higher is better
                if value >= benchmark["excellent"]:
                    interpretation["rating"] = "Excellent"
                    interpretation["message"] = (
                        "Performance significantly exceeds industry standards"
                    )
                elif value >= benchmark["good"]:
                    interpretation["rating"] = "Good"
                    interpretation["message"] = (
                        f"Above average performance for {self.industry} industry"
                    )
                elif value >= benchmark["acceptable"]:
                    interpretation["rating"] = "Acceptable"
                    interpretation["message"] = "Meets industry standards"
                else:
                    interpretation["rating"] = "Poor"
                    interpretation["message"] = "Below industry standards - attention needed"

            elif ratio_name == "debt_to_equity":
                # Lower is better
                if value <= benchmark["excellent"]:
                    interpretation["rating"] = "Excellent"
                    interpretation["message"] = "Very conservative capital structure"
                elif value <= benchmark["good"]:
                    interpretation["rating"] = "Good"
                    interpretation["message"] = "Healthy leverage level"
                elif value <= benchmark["acceptable"]:
                    interpretation["rating"] = "Acceptable"
                    interpretation["message"] = "Moderate leverage"
                else:
                    interpretation["rating"] = "Poor"
                    interpretation["message"] = "High leverage - potential risk"

            elif ratio_name == "pe_ratio":
                # Context-dependent
                if value > 0:
                    if value < benchmark["undervalued"]:
                        interpretation["rating"] = "Potentially Undervalued"
                        interpretation["message"] = (
                            f"Trading below typical {self.industry} multiples"
                        )
                    elif value < benchmark["fair"]:
                        interpretation["rating"] = "Fair Value"
                        interpretation["message"] = "In line with industry averages"
                    elif value < benchmark["growth"]:
                        interpretation["rating"] = "Growth Premium"
                        interpretation["message"] = "Market pricing in growth expectations"
                    else:
                        interpretation["rating"] = "Expensive"
                        interpretation["message"] = "High valuation relative to industry"

        # Add specific recommendations
        interpretation["recommendation"] = self._get_recommendation(
            ratio_name, interpretation["rating"]
        )

        return interpretation

    def _get_recommendation(self, ratio_name: str, rating: str) -> str:
        """Generate actionable recommendations based on ratio and rating."""
        recommendations = {
            "current_ratio": {
                "Poor": "Consider improving working capital management, reducing short-term debt, or increasing liquid assets",
                "Acceptable": "Monitor liquidity closely and consider building additional cash reserves",
                "Good": "Maintain current liquidity management practices",
                "Excellent": "Strong liquidity position - consider productive use of excess cash",
            },
            "debt_to_equity": {
                "Poor": "High leverage increases financial risk - consider debt reduction strategies",
                "Acceptable": "Monitor debt levels and ensure adequate interest coverage",
                "Good": "Balanced capital structure - maintain current approach",
                "Excellent": "Conservative leverage - may consider strategic use of debt for growth",
            },
            "roe": {
                "Poor": "Focus on improving operational efficiency and profitability",
                "Acceptable": "Explore opportunities to enhance returns through operational improvements",
                "Good": "Solid returns - continue current strategies",
                "Excellent": "Outstanding performance - ensure sustainability of high returns",
            },
            "pe_ratio": {
                "Potentially Undervalued": "May present buying opportunity if fundamentals are solid",
                "Fair Value": "Reasonably priced relative to industry peers",
                "Growth Premium": "Ensure growth prospects justify premium valuation",
                "Expensive": "Consider valuation risk - ensure fundamentals support high multiple",
            },
        }

        if ratio_name in recommendations and rating in recommendations[ratio_name]:
            return recommendations[ratio_name][rating]

        return "Continue monitoring this metric"

    def analyze_trend(
        self, ratio_name: str, values: list[float], periods: list[str]
    ) -> dict[str, Any]:
        """
        Analyze trend in a ratio over time.

        Args:
            ratio_name: Name of the ratio
            values: List of ratio values
            periods: List of period labels

        Returns:
            Trend analysis dictionary
        """
        if len(values) < 2:
            return {
                "trend": "Insufficient data",
                "message": "Need at least 2 periods for trend analysis",
            }

        # Calculate trend
        first_value = values[0]
        last_value = values[-1]
        change = last_value - first_value
        pct_change = (change / abs(first_value)) * 100 if first_value != 0 else 0

        # Determine trend direction
        if abs(pct_change) < 5:
            trend = "Stable"
        elif pct_change > 0:
            trend = "Improving" if ratio_name != "debt_to_equity" else "Deteriorating"
        else:
            trend = "Deteriorating" if ratio_name != "debt_to_equity" else "Improving"

        return {
            "trend": trend,
            "change": change,
            "pct_change": pct_change,
            "message": f"{ratio_name} has {'increased' if change > 0 else 'decreased'} by {abs(pct_change):.1f}% from {periods[0]} to {periods[-1]}",
            "values": list(zip(periods, values, strict=False)),
        }

    def generate_report(self, ratios: dict[str, Any]) -> str:
        """
        Generate a comprehensive interpretation report.

        Args:
            ratios: Dictionary of calculated ratios

        Returns:
            Formatted report string
        """
        report_lines = [
            f"Financial Analysis Report - {self.industry.title()} Industry Context",
            "=" * 70,
            "",
        ]

        for category, category_ratios in ratios.items():
            report_lines.append(f"\n{category.upper()} ANALYSIS")
            report_lines.append("-" * 40)

            for ratio_name, value in category_ratios.items():
                if isinstance(value, (int, float)):
                    interpretation = self.interpret_ratio(ratio_name, value)
                    report_lines.append(f"\n{ratio_name.replace('_', ' ').title()}:")
                    report_lines.append(f"  Value: {value:.2f}")
                    report_lines.append(f"  Rating: {interpretation['rating']}")
                    report_lines.append(f"  Analysis: {interpretation['message']}")
                    report_lines.append(f"  Action: {interpretation['recommendation']}")

        return "\n".join(report_lines)


def perform_comprehensive_analysis(
    ratios: dict[str, Any],
    industry: str = "general",
    historical_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Perform comprehensive ratio analysis with interpretations.

    Args:
        ratios: Calculated financial ratios
        industry: Industry sector for benchmarking
        historical_data: Optional historical ratio data for trend analysis

    Returns:
        Complete analysis with interpretations and recommendations
    """
    interpreter = RatioInterpreter(industry)
    analysis = {
        "current_analysis": {},
        "trend_analysis": {},
        "overall_health": {},
        "recommendations": [],
    }

    # Analyze current ratios
    for category, category_ratios in ratios.items():
        analysis["current_analysis"][category] = {}
        for ratio_name, value in category_ratios.items():
            if isinstance(value, (int, float)):
                analysis["current_analysis"][category][ratio_name] = interpreter.interpret_ratio(
                    ratio_name, value
                )

    # Perform trend analysis if historical data provided
    if historical_data:
        for ratio_name, historical_values in historical_data.items():
            if "values" in historical_values and "periods" in historical_values:
                analysis["trend_analysis"][ratio_name] = interpreter.analyze_trend(
                    ratio_name, historical_values["values"], historical_values["periods"]
                )

    # Generate overall health assessment
    analysis["overall_health"] = _assess_overall_health(analysis["current_analysis"])

    # Generate key recommendations
    analysis["recommendations"] = _generate_key_recommendations(analysis)

    # Add formatted report
    analysis["report"] = interpreter.generate_report(ratios)

    return analysis


def _assess_overall_health(current_analysis: dict[str, Any]) -> dict[str, str]:
    """Assess overall financial health based on ratio analysis."""
    ratings = []
    for _category, category_analysis in current_analysis.items():
        for _ratio_name, ratio_analysis in category_analysis.items():
            if "rating" in ratio_analysis:
                ratings.append(ratio_analysis["rating"])

    # Simple scoring system
    score_map = {
        "Excellent": 4,
        "Good": 3,
        "Acceptable": 2,
        "Poor": 1,
        "Fair Value": 3,
        "Potentially Undervalued": 3,
        "Growth Premium": 2,
        "Expensive": 1,
    }

    scores = [score_map.get(rating, 2) for rating in ratings]
    avg_score = sum(scores) / len(scores) if scores else 0

    if avg_score >= 3.5:
        health = "Excellent"
        message = "Company shows strong financial health across most metrics"
    elif avg_score >= 2.5:
        health = "Good"
        message = "Overall healthy financial position with some areas for improvement"
    elif avg_score >= 1.5:
        health = "Fair"
        message = "Mixed financial indicators - attention needed in several areas"
    else:
        health = "Poor"
        message = "Significant financial challenges requiring immediate attention"

    return {"status": health, "message": message, "score": f"{avg_score:.1f}/4.0"}


def _generate_key_recommendations(analysis: dict[str, Any]) -> list[str]:
    """Generate prioritized recommendations based on analysis."""
    recommendations = []

    # Check for critical issues
    for _category, category_analysis in analysis["current_analysis"].items():
        for ratio_name, ratio_analysis in category_analysis.items():
            if ratio_analysis.get("rating") == "Poor":
                recommendations.append(
                    f"Priority: Address {ratio_name.replace('_', ' ')} - {ratio_analysis.get('recommendation', '')}"
                )

    # Add trend-based recommendations
    for ratio_name, trend in analysis.get("trend_analysis", {}).items():
        if trend.get("trend") == "Deteriorating":
            recommendations.append(
                f"Monitor: {ratio_name.replace('_', ' ')} showing negative trend"
            )

    # Add general recommendations if healthy
    if not recommendations:
        recommendations.append("Continue current financial management practices")
        recommendations.append("Consider strategic growth opportunities")

    return recommendations[:5]  # Return top 5 recommendations
