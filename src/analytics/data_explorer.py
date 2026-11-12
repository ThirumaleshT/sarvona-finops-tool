"""
Data Explorer Module
Multi-dimensional query interface for cost data analysis
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
import pandas as pd
from abc import ABC, abstractmethod


class QueryField:
    """Represents a field that can be queried"""
    def __init__(self, name: str, field_type: str = "string",
                 is_groupable: bool = True, is_filterable: bool = True):
        self.name = name
        self.field_type = field_type
        self.is_groupable = is_groupable
        self.is_filterable = is_filterable


@dataclass
class SavedQuery:
    id: str
    name: str
    description: str
    query: Dict[str, Any]
    created_by: str = ""
    is_shared: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)


@dataclass
class QueryResult:
    data: pd.DataFrame
    query_time_ms: int
    row_count: int
    cache_key: str = ""
    warnings: List[str] = field(default_factory=list)


class CostDataSource:
    """Abstract base class for cost data sources"""

    def __init__(self):
        self.cache = {}

    @abstractmethod
    def get_fields(self) -> List[QueryField]:
        """Return available query fields"""
        pass

    @abstractmethod
    def query(self, filters: Dict[str, Any], group_by: List[str],
              select: List[str], limit: int = 1000) -> QueryResult:
        """Execute a query and return results"""
        pass


class VirtualCostDataSource(CostDataSource):
    """Virtual data source for testing and demo purposes"""

    def __init__(self, sample_data: List[Dict[str, Any]]):
        super().__init__()
        self.sample_data = sample_data

    def get_fields(self) -> List[QueryField]:
        return [
            QueryField("provider", "string"),
            QueryField("service", "string"),
            QueryField("resource_id", "string"),
            QueryField("resource_name", "string"),
            QueryField("cost", "number"),
            QueryField("monthly_cost", "number"),
            QueryField("date", "date"),
            QueryField("tags.team", "string"),
            QueryField("tags.environment", "string"),
            QueryField("tags.project", "string"),
            QueryField("region", "string"),
            QueryField("type", "string")
        ]

    def query(self, filters: Dict[str, Any], group_by: List[str],
              select: List[str], limit: int = 1000) -> QueryResult:
        import time
        start_time = time.time()

        df = pd.DataFrame(self.sample_data) if self.sample_data else pd.DataFrame()

        # Apply filters
        for key, value in filters.items():
            if key == "provider":
                df = df[df.get("provider", "").str.contains(value, case=False, na=False)]
            elif key == "service":
                df = df[df.get("service", "").str.contains(value, case=False, na=False)]
            elif key == "cost__gte":
                df = df[df.get("monthly_cost", df.get("cost", 0)) >= value]
            elif key == "cost__lte":
                df = df[df.get("monthly_cost", df.get("cost", 0)) <= value]
            elif "tags." in key:
                tag_key = key.replace("tags.", "")
                df = df[df.get("tags", {}).apply(lambda x: x.get(tag_key, "") if isinstance(x, dict) else "")]

        # Apply grouping
        if group_by:
            cost_col = "monthly_cost" if "monthly_cost" in df.columns else "cost"
            if cost_col in df.columns:
                df = df.groupby(group_by)[cost_col].sum().reset_index()

        # Apply limit
        df = df.head(limit)

        query_time = int((time.time() - start_time) * 1000)

        return QueryResult(
            data=df,
            query_time_ms=query_time,
            row_count=len(df),
            cache_key=str(hash(str(filters) + str(group_by)))
        )


class DataExplorer:
    """Main data explorer class for querying cost data"""

    def __init__(self, data_source: CostDataSource):
        self.data_source = data_source
        self.saved_queries: List[SavedQuery] = []
        self._query_history: List[Dict[str, Any]] = []

    def get_available_fields(self) -> List[QueryField]:
        """Get all available queryable fields"""
        return self.data_source.get_fields()

    def execute_query(self, filters: Dict[str, Any] = None,
                     group_by: List[str] = None, select: List[str] = None,
                     limit: int = 1000, use_cache: bool = True) -> QueryResult:
        """Execute a data query with filters, grouping, and selection"""
        filters = filters or {}
        group_by = group_by or []
        select = select or []

        # Check cache
        cache_key = f"{str(filters)}_{'_'.join(group_by)}"
        if use_cache and cache_key in self.data_source.cache:
            return self.data_source.cache[cache_key]

        result = self.data_source.query(filters, group_by, select, limit)

        # Cache result
        if use_cache:
            self.data_source.cache[cache_key] = result

        # Record query history
        self._query_history.append({
            "timestamp": datetime.now().isoformat(),
            "filters": filters,
            "group_by": group_by,
            "row_count": result.row_count,
            "query_time_ms": result.query_time_ms
        })

        return result

    def save_query(self, name: str, description: str,
                   filters: Dict[str, Any], group_by: List[str],
                   select: List[str], created_by: str = "") -> SavedQuery:
        """Save a query for reuse"""
        query_id = f"q_{len(self.saved_queries) + 1}_{int(datetime.now().timestamp())}"
        saved_query = SavedQuery(
            id=query_id,
            name=name,
            description=description,
            query={
                "filters": filters,
                "group_by": group_by,
                "select": select,
                "limit": 1000
            },
            created_by=created_by
        )
        self.saved_queries.append(saved_query)
        return saved_query

    def run_saved_query(self, query_id: str) -> QueryResult:
        """Run a previously saved query"""
        query = next((q for q in self.saved_queries if q.id == query_id), None)
        if not query:
            raise ValueError(f"Query {query_id} not found")

        query.last_used = datetime.now()
        q = query.query

        return self.execute_query(
            filters=q.get("filters", {}),
            group_by=q.get("group_by", []),
            select=q.get("select", []),
            limit=q.get("limit", 1000)
        )

    def get_saved_queries(self) -> List[SavedQuery]:
        """Get all saved queries"""
        return self.saved_queries

    def delete_saved_query(self, query_id: str) -> bool:
        """Delete a saved query"""
        for i, q in enumerate(self.saved_queries):
            if q.id == query_id:
                self.saved_queries.pop(i)
                return True
        return False

    def export_results(self, result: QueryResult, format: str = "json") -> str:
        """Export query results to various formats"""
        if format == "json":
            return result.data.to_json(orient="records", indent=2, date_format="iso")
        elif format == "csv":
            return result.data.to_csv(index=False)
        elif format == "excel":
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                result.data.to_excel(writer, index=False)
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_query_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent query history"""
        return self._query_history[-limit:]

    def get_suggestions(self, partial: str) -> List[str]:
        """Get autocomplete suggestions for query fields"""
        fields = self.get_available_fields()
        suggestions = [f.name for f in fields if partial.lower() in f.name.lower()]
        return suggestions

    def validate_query(self, filters: Dict[str, Any], group_by: List[str] = None) -> List[str]:
        """Validate query and return any warnings"""
        warnings = []

        if not filters and not group_by:
            warnings.append("No filters or grouping specified - this will return all data")

        for key in filters.keys():
            if "tags." in key:
                warnings.append(f"Tag filters may be slow for large datasets")

        return warnings


class QueryTemplate:
    """Predefined query templates for common analyses"""

    @staticmethod
    def top_services(hours: int = 730, limit: int = 10) -> Dict[str, Any]:
        """Get top services by cost"""
        return {
            "filters": {"date__gte": f"now-{hours}h"},
            "group_by": ["service", "provider"],
            "select": ["service", "provider", "sum(cost) as total_cost"],
            "limit": limit
        }

    @staticmethod
    def cost_by_team(limit: int = 20) -> Dict[str, Any]:
        """Get cost allocation by team"""
        return {
            "filters": {},
            "group_by": ["tags.team", "provider"],
            "select": ["tags.team as team", "provider", "sum(monthly_cost) as monthly_cost"],
            "limit": limit
        }

    @staticmethod
    def anomaly_investigation(service: str = "") -> Dict[str, Any]:
        """Query for investigating cost anomalies"""
        return {
            "filters": {"service": service} if service else {},
            "group_by": ["resource_id", "resource_name", "provider"],
            "select": ["resource_id", "resource_name", "provider", "sum(monthly_cost) as monthly_cost"],
            "order_by": "monthly_cost DESC",
            "limit": 50
        }

    @staticmethod
    def monthly_trend(months: int = 12) -> Dict[str, Any]:
        """Get monthly cost trend"""
        return {
            "filters": {"date__gte": f"now-{months}m"},
            "group_by": ["date"],
            "select": ["date", "sum(monthly_cost) as monthly_cost"],
            "limit": months
        }

    @staticmethod
    def tag_coverage() -> Dict[str, Any]:
        """Analyze tag completeness"""
        return {
            "filters": {},
            "group_by": ["tags.environment", "tags.team"],
            "select": ["tags.environment", "tags.team", "count() as resource_count", "sum(monthly_cost) as total_cost"],
            "limit": 100
        }


# Factory function to create a configured explorer
def create_explorer(sample_data: List[Dict[str, Any]]) -> DataExplorer:
    """Create a data explorer with sample data for testing"""
    source = VirtualCostDataSource(sample_data)
    return DataExplorer(source)