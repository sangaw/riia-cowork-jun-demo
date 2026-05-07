"""Repository for agent_build_runs and agent_build_agents tables."""
from typing import Optional

from sqlalchemy.orm import Session

from rita.models.agent_builds import AgentBuildAgentModel, AgentBuildRunModel


class AgentBuildRepository:
    """Read-only repository for agent build pipeline run data."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_with_agents(
        self,
        limit: int = 20,
        app_filter: Optional[str] = None,
    ) -> list[AgentBuildRunModel]:
        """Return run rows ordered by run_id descending, optionally filtered by app."""
        q = self._db.query(AgentBuildRunModel)
        if app_filter is not None:
            q = q.filter(AgentBuildRunModel.app == app_filter)
        return q.order_by(AgentBuildRunModel.run_id.desc()).limit(limit).all()

    def list_all_agents(self) -> list[AgentBuildAgentModel]:
        """Return all agent rows."""
        return self._db.query(AgentBuildAgentModel).all()
