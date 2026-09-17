from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool, FileWriterTool


@CrewBase
class PasteGateCrew:
    """Paste Gate — PII and secret redaction crew."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def scrubber(self) -> Agent:
        return Agent(
            config=self.agents_config["scrubber"],
            tools=[FileReadTool(), FileWriterTool()],
            verbose=True,
        )

    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config["judge"],
            tools=[FileReadTool()],
            verbose=True,
        )

    @agent
    def reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["reporter"],
            tools=[FileWriterTool()],
            verbose=True,
        )

    @task
    def scrub_task(self) -> Task:
        return Task(config=self.tasks_config["scrub_task"])

    @task
    def judge_task(self) -> Task:
        return Task(config=self.tasks_config["judge_task"])

    @task
    def report_task(self) -> Task:
        return Task(config=self.tasks_config["report_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
