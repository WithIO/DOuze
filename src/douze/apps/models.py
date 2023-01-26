import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Text, Type, Union

from typefit.narrows import DateTime

from douze.models import (
    Collection,
    MongoVersion,
    MySqlVersion,
    PostgreSqlVersion,
    RedisVersion,
    Version,
)
from douze.types import Uuid

__all__ = [
    "App",
    "AppCollection",
    "AppDatabaseSpec",
    "AppDeployment",
    "AppDeploymentCollection",
    "AppDomainSpec",
    "AppFunctionSpec",
    "AppJobSpec",
    "AppServiceSpec",
    "AppSpec",
    "AppStaticSitesSpec",
    "AppVariableDefinition",
    "AppWorkerSpec",
    "Basic",
    "Domain",
    "Engine",
    "Function",
    "GitHubSourceSpec",
    "GitLabSourceSpec",
    "GitSourceSpec",
    "ImageSourceSpec",
    "Job",
    "MachineSize",
    "Professional",
    "Region",
    "RegionSlug",
    "RouteSpec",
    "Service",
    "StaticSites",
    "TLSVersion",
    "Worker",
    # reexport
    "get_engine_versions",
    "validate_db_version",
]


class TLSVersion(Enum):
    TLS1_2 = "1.2"
    TLS1_3 = "1.3"


class RegionSlug(Enum):
    AMS = "ams"
    FRA = "fra"
    NYC = "nyc"


class DeployPhase(Enum):
    PRE_DEPLOY = "PRE_DEPLOY"
    POST_DEPLOY = "POST_DEPLOY"


@dataclass
class AppDomainSpec:
    DOMAIN_PATTERN = re.compile(
        r"^([a-zA-Z0-9]+(-+[a-zA-Z0-9]+)*\.)+(xn--)?[a-zA-Z0-9]{2,}\.?$"
    )

    class DomainType(Enum):
        UNSPECIFIED = "UNSPECIFIED"
        DEFAULT = "DEFAULT"
        PRIMARY = "PRIMARY"
        ALIAS = "ALIAS"

    domain: Text
    minimum_tls_version: Optional[TLSVersion] = TLSVersion.TLS1_2
    type: DomainType = DomainType.UNSPECIFIED
    zone: Optional[Text] = None
    wildcard: bool = False

    def __post_init__(self):
        if not self.DOMAIN_PATTERN.match(self.domain):
            raise ValueError(f"invalid domain {self.domain}")


@dataclass
class GitSourceSpec:
    repo_clone_url: Text
    branch: Text


@dataclass
class GitHubSourceSpec:
    repo: Text
    branch: Text
    deploy_on_push: Optional[bool] = False


@dataclass
class GitLabSourceSpec(GitHubSourceSpec):
    pass


@dataclass
class ImageSourceSpec:
    class Registry(Enum):
        DOCR = "DOCR"
        DOCKERHUB = "DOCKER_HUB"

    repository: Text
    registry_type: Registry
    tag: Text = "latest"
    registry: Optional[Text] = None


@dataclass
class AppVariableDefinition:
    class Scope(Enum):
        UNSET = "UNSET"
        RUN_TIME = "RUN_TIME"
        BUILD_TIME = "BUILD_TIME"
        RUN_AND_BUILD_TIME = "RUN_AND_BUILD_TIME"

    class VarType(Enum):
        GENERAL = "GENERAL"
        SECRET = "SECRET"  # nosec B105

    key: Text
    value: Text = None
    type: VarType = VarType.GENERAL
    scope: Scope = Scope.RUN_AND_BUILD_TIME


@dataclass
class RouteSpec:
    path: Optional[Text] = "/"
    preserve_path_prefix: bool = True


@dataclass
class AppCommonRunnerSpec:
    """
    Members
    -------
    name
        The name. Must be unique across all components within the same app.
    git
    github
    gitlab
    image
        Only one of these may appear simultaneously.
    dockerfile_path
        The path to the Dockerfile relative to the root of the repo. If set, it will be used to build this component.
        Otherwise, App Platform will attempt to build it using buildpacks.
    """

    name: Text
    git: Optional[GitSourceSpec] = None
    github: Optional[GitHubSourceSpec] = None
    gitlab: Optional[GitLabSourceSpec] = None
    image: Optional[ImageSourceSpec] = None
    dockerfile_path: Optional[Text] = None
    build_command: Optional[Text] = None
    run_command: Optional[Text] = None
    source_dir: Optional[Text] = "/"  # REVIEW
    envs: List[AppVariableDefinition] = field(default_factory=list)
    environment_slug: Text = None
    log_destinations: Any = None

    def __post_init__(self):
        validate_name(self.name)


class MachineSize(Enum):
    pass


class Basic(MachineSize):
    XXS = "basic-xxs"
    XS = "basic-xs"
    S = "basic-s"
    M = "basic-m"


class Professional(MachineSize):
    XXS = "professional-xxs"
    XS = "professional-xs"
    S = "professional-s"
    M = "professional-m"
    L = "professional-1l"
    XL = "professional-xl"


@dataclass
class AppWorkerSpec(AppCommonRunnerSpec):

    instance_count: Optional[int] = 1
    instance_size_slug: Optional[Union[Text, MachineSize]] = Basic.XS

    def __post_init__(self):
        self.instance_size_slug = self._convert_instance_size()

    def _convert_instance_size(self):
        """
        Convert between Text and enum.
        """
        size = self.instance_size_slug or Basic.XS
        if isinstance(size, Text):
            try:
                size = Basic(size)
            except ValueError:
                size = Professional(size)
        elif type(size) not in (Basic, Professional):
            raise ValueError(f"Unknown size {size}")

        return size


@dataclass
class AppServiceSpec(AppWorkerSpec):
    cors: Optional[Any] = None
    health_check: Optional[Any] = None
    http_port: Optional[int] = None
    internal_ports: Optional[List[int]] = field(default_factory=list)
    routes: Optional[List[RouteSpec]] = field(default_factory=list)


@dataclass
class AppJobSpec(AppWorkerSpec):
    class Kind(Enum):
        PRE_DEPLOY = "PRE_DEPLOY"
        POST_DEPLOY = "POST_DEPLOY"
        FAILED_DEPLOY = "FAILED_DEPLOY"

    kind: Optional[Kind] = None


@dataclass
class AppFunctionSpec:
    # Note: we don't have any of these yet. Untested
    name: Text
    cors: Optional[Any] = None
    routes: Optional[List[RouteSpec]] = field(default_factory=list)
    git: Optional[GitSourceSpec] = None
    github: Optional[GitHubSourceSpec] = None
    gitlab: Optional[GitLabSourceSpec] = None
    source_dir: Optional[Text] = None
    alerts: Optional[Any] = None
    envs: Optional[List[AppVariableDefinition]] = field(default_factory=list)
    log_destinations: Optional[Any] = None

    def __post_init__(self):
        validate_name(self.name)


@dataclass
class AppStaticSitesSpec(AppCommonRunnerSpec):
    # Note: we don't have one yet. This is untested
    index_document: Optional[Text] = None
    error_document: Optional[Text] = None
    catchall_document: Optional[Text] = None
    output_dir: Optional[Text] = None


class Engine(Enum):
    mysql = "MYSQL"
    pg = "PG"
    redis = "REDIS"
    mongo = "MONGO"


@dataclass
class AppDatabaseSpec:
    """
    Represents a managed database instance.
    We assume all databases are what DO calls "production" databases,
    that need to be configured separately.
    """

    name: Text
    cluster_name: Optional[Text] = None
    version: Optional[Union[Text, Type[Version]]] = None
    db_name: Optional[Text] = None
    db_user: Optional[Text] = None
    production: bool = False
    engine: Engine = Engine.pg
    size: Union[Text, Type[MachineSize]] = None

    def __post_init__(self):
        """
        Check the validity of the object.
        Raises exceptions for incorrect properties or combinations of them
        """
        self.production = self._validate_production()
        self._validate_name()
        self.version = validate_db_version(self.engine, self.version)
        self._validate_cluster_name()
        self._validate_db_params()

    def _validate_production(self) -> bool:
        """
        If a cluster name is given, it's a production database.
        """
        if self.cluster_name:
            return True

        return self.production

    def _validate_cluster_name(self):
        """
        Ensure that production databases have a cluster name
        """
        if self.production and not self.cluster_name:
            raise ValueError("production databases require 'cluster_name'")

    def _validate_name(self):
        """
        Ensure there is a name in production databases.
        If a name is provided, verify it
        """
        if self.production:
            validate_name(self.name)
        elif self.name is not None:
            validate_name(self.name)

    def _validate_db_params(self):
        """
        Postgres and MySQL require database credentials
        Redis does not support either
        """
        if self.engine in (Engine.pg, Engine.mysql):
            if self.production and not (self.db_user and self.db_name):
                raise ValueError(
                    f"{self.engine.value} requires 'db_name' and 'db_user'"
                )

        if self.engine == Engine.redis:
            if self.db_user or self.db_name:
                raise ValueError(
                    f"{self.engine.value} does not support 'db_name' nor 'db_user'"
                )


@dataclass
class AppSpec(dict):
    name: Text
    region: RegionSlug = RegionSlug.AMS
    domains: List[AppDomainSpec] = field(default_factory=list)
    services: List[AppServiceSpec] = field(default_factory=list)
    jobs: List[AppJobSpec] = field(default_factory=list)
    workers: List[AppWorkerSpec] = field(default_factory=list)
    functions: List[Any] = field(default_factory=list)
    databases: List[AppDatabaseSpec] = field(default_factory=list)

    def __post_init__(self):
        validate_name(self.name)


# App Deployment


@dataclass
class HashName:
    name: Text
    source_commit_hash: Optional[Text] = None
    source_image_digest: Optional[Text] = None


@dataclass
class Job(HashName):
    pass


@dataclass
class Function(HashName):
    namespace: Optional[Text] = None


@dataclass
class Service(HashName):
    pass


@dataclass
class Worker(HashName):
    pass


@dataclass
class StaticSites(HashName):
    pass


# App


@dataclass
class AppDeployment:
    class Phase(Enum):
        UNKNOWN = "UNKNOWN"
        PENDING_BUILD = "PENDING_BUILD"
        BUILDING = "BUILDING"
        PENDING_DEPLOY = "PENDING_DEPLOY"
        DEPLOYING = "DEPLOYING"
        ACTIVE = "ACTIVE"
        SUPERSEDED = "SUPERSEDED"
        ERROR = "ERROR"
        CANCELED = "CANCELED"

    id: Uuid
    cause: Text
    created_at: DateTime
    tier_slug: Text
    spec: AppSpec
    updated_at: Optional[DateTime] = None
    phase: Optional[Phase] = field(default=Phase.UNKNOWN)
    phase_last_updated_at: Optional[DateTime] = None
    jobs: Optional[List[Job]] = field(default_factory=list)
    services: Optional[List[Service]] = field(default_factory=list)
    functions: Optional[List[Function]] = field(default_factory=list)
    static_sites: Optional[List[StaticSites]] = field(default_factory=list)
    workers: Optional[List[Worker]] = field(default_factory=list)
    cloned_from: Optional[Uuid] = None


@dataclass
class DomainSpec:
    class Type(Enum):
        DEFAULT = "DEFAULT"
        PRIMARY = "PRIMARY"
        ALIAS = "ALIAS"

    domain: Text
    type: Type
    minimum_tls_version: TLSVersion
    wildcard: bool = False
    zone: Optional[Text] = None


@dataclass
class Domain:
    class Phase(Enum):
        UNKNOWN = "UNKNOWN"
        PENDING = "PENDING"
        CONFIGURING = "CONFIGURING"
        ACTIVE = "ACTIVE"
        ERROR = "ERROR"

    id: Uuid
    phase: Phase
    spec: DomainSpec


@dataclass
class Region:
    label: Text
    slug: Text
    default: bool = False
    disabled: bool = False


@dataclass
class App:
    id: Uuid
    created_at: DateTime
    spec: AppSpec
    default_ingress: Optional[Text] = None
    domains: List[Domain] = field(default_factory=list)
    pinned_deployment: Optional[AppDeployment] = None
    active_deployment: Optional[AppDeployment] = None
    in_progress_deployment: Optional[AppDeployment] = None
    updated_at: Optional[DateTime] = None
    tier_slug: Optional[Text] = None
    region: Optional[Region] = None
    owner_uuid: Optional[Text] = None
    live_domain: Optional[Text] = None
    live_url: Optional[Text] = None
    live_url_base: Optional[Text] = None
    last_deployment_created_at: Optional[DateTime] = None


@dataclass
class AppCollection(Collection):
    apps: List[App] = field(default_factory=list)


@dataclass
class AppDeploymentCollection(Collection):
    deployments: List[AppDeployment] = field(default_factory=list)


# The DO API reference mentions some basic validations
def validate_name(name: Text):
    if not re.match(r"^[a-z][a-z\d-]{0,30}[a-z\d]$", name):
        raise ValueError(f"invalid name {name}")


def get_engine_versions(engine: Engine) -> Type[Version]:
    """
    Select the correct enum type for this DB Engine.
    """
    version = {
        Engine.pg: PostgreSqlVersion,
        Engine.mysql: MySqlVersion,
        Engine.mongo: MongoVersion,
        Engine.redis: RedisVersion,
    }.get(engine, None)

    if version is None:
        raise ValueError(f"unknown engine {engine}")

    return version


def validate_db_version(
    engine: Engine, version: Union[Text, Type[Version]] = None
) -> Type[Version]:
    """
    Type checking for the possible enums, one for each Engine type.
    If `version` is None, the latest version for the selected engine
    is returned. If it's set to a legal value for the engine, it's returned
    untouched.
    """

    ng_version = get_engine_versions(engine)

    if version is None:
        version = get_engine_versions(engine).latest()
    elif ng_version is not None:
        if isinstance(version, Text):
            version = ng_version(version)
    else:
        raise ValueError(f"unknown version {version} for DB engine {engine}")

    return version


def validate_machine_size(
    size: Union[Text, Type[MachineSize]] = None
) -> Type[MachineSize]:
    size = size or Basic.XS
    if isinstance(size, Text):
        try:
            size = Basic(size)
        except ValueError:
            size = Professional(size)
    elif type(size) not in (Basic, Professional):
        raise ValueError(f"Unknown size {size}")

    return size
