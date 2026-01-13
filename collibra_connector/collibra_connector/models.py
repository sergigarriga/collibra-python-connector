"""
Pydantic models for Collibra API responses.

This module provides typed models for all Collibra resources, enabling
full IDE autocompletion, validation, and type safety.

Example:
    >>> asset = conn.asset.get_asset("uuid")  # Returns AssetModel
    >>> print(asset.name)
    >>> print(asset.status.name)
    >>> print(asset.type.id)
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, Iterator, List, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Type variable for generic paginated responses
T = TypeVar('T', bound='BaseCollibraModel')


class ResourceType(str, Enum):
    """Enum for Collibra resource types."""
    ASSET = "Asset"
    DOMAIN = "Domain"
    COMMUNITY = "Community"
    USER = "User"
    ATTRIBUTE = "Attribute"
    RELATION = "Relation"
    COMMENT = "Comment"
    RESPONSIBILITY = "Responsibility"
    WORKFLOW = "Workflow"
    STATUS = "Status"
    ASSET_TYPE = "AssetType"
    DOMAIN_TYPE = "DomainType"
    ATTRIBUTE_TYPE = "AttributeType"
    RELATION_TYPE = "RelationType"


class BaseCollibraModel(BaseModel):
    """Base class for all Collibra models with common configuration."""
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",  # Allow extra fields from API
        str_strip_whitespace=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary with camelCase keys."""
        return self.model_dump(by_alias=True, exclude_none=True)

    def to_json(self) -> str:
        """Convert model to JSON string."""
        return self.model_dump_json(by_alias=True, exclude_none=True)


class ResourceReference(BaseCollibraModel):
    """Reference to another resource (lightweight representation)."""
    id: str
    resource_type: Optional[str] = Field(default=None, alias="resourceType")
    name: Optional[str] = None
    user_name: Optional[str] = Field(default=None, alias="userName")
    first_name: Optional[str] = Field(default=None, alias="firstName")
    last_name: Optional[str] = Field(default=None, alias="lastName")

    @property
    def display_name(self) -> str:
        """Get the most descriptive name available."""
        if self.name:
            return self.name
        if self.first_name or self.last_name:
            parts = [self.first_name, self.last_name]
            return " ".join(p for p in parts if p)
        return self.user_name or self.id

    def __str__(self) -> str:
        return self.display_name

    def __repr__(self) -> str:
        return f"ResourceReference(id={self.id!r}, name={self.display_name!r})"


class TypedResourceReference(ResourceReference):
    """Resource reference with additional type information."""
    public_id: Optional[str] = Field(default=None, alias="publicId")
    description: Optional[str] = None


class NamedResource(BaseCollibraModel):
    """Base class for resources with id, name, and description."""
    id: str
    resource_type: Optional[str] = Field(default=None, alias="resourceType")
    name: Optional[str] = None
    description: Optional[str] = None

    def __str__(self) -> str:
        return self.name or self.id

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, name={self.name!r})"


class TimestampMixin:
    """Mixin for resources with created/modified timestamps (fields only)."""
    pass


def _get_created_datetime(self: Any) -> Optional[datetime]:
    """Get created_on as datetime object."""
    created_on = getattr(self, 'created_on', None)
    if created_on:
        return datetime.fromtimestamp(created_on / 1000)
    return None


def _get_last_modified_datetime(self: Any) -> Optional[datetime]:
    """Get last_modified_on as datetime object."""
    last_modified_on = getattr(self, 'last_modified_on', None)
    if last_modified_on:
        return datetime.fromtimestamp(last_modified_on / 1000)
    return None


# ============================================================================
# Status Model
# ============================================================================

class StatusModel(NamedResource):
    """Collibra Status Model."""
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    created_by: Optional[str] = Field(default=None, alias="createdBy")
    last_modified_by: Optional[str] = Field(default=None, alias="lastModifiedBy")
    signifies_approval: Optional[bool] = Field(default=None, alias="signifiesApproval")

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)


# ============================================================================
# Asset Type Model
# ============================================================================

class AssetTypeModel(NamedResource):
    """Collibra Asset Type Model."""
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    created_by: Optional[str] = Field(default=None, alias="createdBy")
    last_modified_by: Optional[str] = Field(default=None, alias="lastModifiedBy")
    public_id: Optional[str] = Field(default=None, alias="publicId")
    symbol_type: Optional[str] = Field(default=None, alias="symbolType")
    acronym_code: Optional[str] = Field(default=None, alias="acronymCode")
    parent: Optional[ResourceReference] = None
    is_meta: Optional[bool] = Field(default=False, alias="isMeta")
    display_name_enabled: Optional[bool] = Field(default=False, alias="displayNameEnabled")
    rating_enabled: Optional[bool] = Field(default=False, alias="ratingEnabled")

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)


# ============================================================================
# Community Model
# ============================================================================

class CommunityModel(NamedResource):
    """Collibra Community Model."""
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    created_by: Optional[str] = Field(default=None, alias="createdBy")
    last_modified_by: Optional[str] = Field(default=None, alias="lastModifiedBy")
    parent: Optional[ResourceReference] = None

    def is_root(self) -> bool:
        """Check if this is a root community (no parent)."""
        return self.parent is None

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)


# ============================================================================
# Domain Model
# ============================================================================

class DomainTypeModel(NamedResource):
    """Collibra Domain Type Model."""
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    public_id: Optional[str] = Field(default=None, alias="publicId")

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)


class DomainModel(NamedResource):
    """Collibra Domain Model."""
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    created_by: Optional[str] = Field(default=None, alias="createdBy")
    last_modified_by: Optional[str] = Field(default=None, alias="lastModifiedBy")
    type: ResourceReference
    community: ResourceReference
    excluded_from_auto_hyperlinking: bool = Field(
        default=False,
        alias="excludedFromAutoHyperlinking"
    )

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)


# ============================================================================
# Asset Model (Core)
# ============================================================================

class AssetModel(NamedResource):
    """
    Collibra Asset Model - the core data object.

    This model represents a Collibra asset with full type information
    and convenient property accessors.

    Example:
        >>> asset = conn.asset.get_asset("uuid")
        >>> print(f"Name: {asset.name}")
        >>> print(f"Type: {asset.type.name}")
        >>> print(f"Status: {asset.status.name}")
        >>> print(f"Domain: {asset.domain.name}")
        >>> if asset.is_approved:
        ...     print("Asset is approved!")
    """
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    created_by: Optional[str] = Field(default=None, alias="createdBy")
    last_modified_by: Optional[str] = Field(default=None, alias="lastModifiedBy")
    display_name: Optional[str] = Field(default=None, alias="displayName")
    type: ResourceReference
    status: ResourceReference
    domain: ResourceReference
    avg_rating: float = Field(default=0.0, alias="avgRating")
    ratings_count: int = Field(default=0, alias="ratingsCount")
    excluded_from_auto_hyperlinking: bool = Field(
        default=False,
        alias="excludedFromAutoHyperlinking"
    )
    articulation_score: Optional[float] = Field(default=None, alias="articulationScore")

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)

    @property
    def effective_name(self) -> str:
        """Get display_name if available, otherwise name."""
        return self.display_name or self.name

    @property
    def type_name(self) -> str:
        """Convenience accessor for type.name."""
        return self.type.name or "Unknown"

    @property
    def status_name(self) -> str:
        """Convenience accessor for status.name."""
        return self.status.name or "Unknown"

    @property
    def domain_name(self) -> str:
        """Convenience accessor for domain.name."""
        return self.domain.name or "Unknown"

    @property
    def has_rating(self) -> bool:
        """Check if asset has any ratings."""
        return self.ratings_count > 0


# ============================================================================
# User Model
# ============================================================================

class UserModel(NamedResource):
    """Collibra User Model."""
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    created_by: Optional[str] = Field(default=None, alias="createdBy")
    last_modified_by: Optional[str] = Field(default=None, alias="lastModifiedBy")
    user_name: Optional[str] = Field(default=None, alias="userName")
    first_name: Optional[str] = Field(default=None, alias="firstName")
    last_name: Optional[str] = Field(default=None, alias="lastName")
    email_address: Optional[str] = Field(default=None, alias="emailAddress")
    gender: Optional[str] = None
    language: Optional[str] = None
    activated: bool = False
    enabled: bool = False
    ldap_user: Optional[bool] = Field(default=None, alias="ldapUser")
    guest_user: Optional[bool] = Field(default=None, alias="guestUser")
    api_user: Optional[bool] = Field(default=None, alias="apiUser")

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.name or self.user_name or "Unknown"

    @property
    def is_active(self) -> bool:
        """Check if user is both activated and enabled."""
        return self.activated and self.enabled


# ============================================================================
# Attribute Model
# ============================================================================

class AttributeTypeModel(NamedResource):
    """Collibra Attribute Type Model."""
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    public_id: Optional[str] = Field(default=None, alias="publicId")
    kind: Optional[str] = None
    statistics_enabled: Optional[bool] = Field(default=False, alias="statisticsEnabled")
    is_integer: Optional[bool] = Field(default=False, alias="isInteger")
    allowed_values: Optional[List[str]] = Field(default=None, alias="allowedValues")

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)


class AttributeModel(BaseCollibraModel):
    """Collibra Attribute Model."""
    id: str
    resource_type: Optional[str] = Field(default=None, alias="resourceType")
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    type: ResourceReference
    value: Any
    asset: Optional[ResourceReference] = None

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)

    @property
    def type_name(self) -> str:
        """Convenience accessor for type.name."""
        return self.type.name or "Unknown"

    @property
    def string_value(self) -> str:
        """Get value as string."""
        if self.value is None:
            return ""
        return str(self.value)


# ============================================================================
# Relation Model
# ============================================================================

class RelationTypeModel(NamedResource):
    """Collibra Relation Type Model."""
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    public_id: Optional[str] = Field(default=None, alias="publicId")
    role: Optional[str] = None
    co_role: Optional[str] = Field(default=None, alias="coRole")
    source_type: Optional[ResourceReference] = Field(default=None, alias="sourceType")
    target_type: Optional[ResourceReference] = Field(default=None, alias="targetType")

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)


class RelationModel(BaseCollibraModel):
    """Collibra Relation Model."""
    id: str
    resource_type: Optional[str] = Field(default=None, alias="resourceType")
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    type: ResourceReference
    source: ResourceReference
    target: ResourceReference
    starting_date: Optional[int] = Field(default=None, alias="startingDate")
    ending_date: Optional[int] = Field(default=None, alias="endingDate")

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)

    @property
    def type_name(self) -> str:
        """Convenience accessor for type.name."""
        return self.type.name or "Unknown"


# ============================================================================
# Responsibility Model
# ============================================================================

class RoleModel(NamedResource):
    """Collibra Role Model."""
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    global_role: Optional[bool] = Field(default=False, alias="global")

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)


class ResponsibilityModel(BaseCollibraModel):
    """Collibra Responsibility Model."""
    id: str
    resource_type: Optional[str] = Field(default=None, alias="resourceType")
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    role: ResourceReference
    owner: ResourceReference
    resource: Optional[ResourceReference] = None
    base_resource: Optional[ResourceReference] = Field(default=None, alias="baseResource")

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)

    @property
    def role_name(self) -> str:
        """Convenience accessor for role.name."""
        return self.role.name or "Unknown"

    @property
    def owner_name(self) -> str:
        """Convenience accessor for owner.name."""
        return self.owner.name or "Unknown"


# ============================================================================
# Comment Model
# ============================================================================

class CommentModel(BaseCollibraModel):
    """Collibra Comment Model."""
    id: str
    resource_type: Optional[str] = Field(default=None, alias="resourceType")
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    created_by: Optional[str] = Field(default=None, alias="createdBy")
    content: str
    base_resource: Optional[ResourceReference] = Field(default=None, alias="baseResource")
    parent: Optional[ResourceReference] = None

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)


# ============================================================================
# Search Models
# ============================================================================

class SearchHighlight(BaseCollibraModel):
    """Search result highlight."""
    field: Optional[str] = None
    values: Optional[List[str]] = None


class SearchResource(BaseCollibraModel):
    """The resource found in search."""
    id: str
    resource_type: Optional[str] = Field(default=None, alias="resourceType")
    name: Optional[str] = None
    display_name: Optional[str] = Field(default=None, alias="displayName")
    description: Optional[str] = None

    @property
    def effective_name(self) -> str:
        """Get display_name if available, otherwise name."""
        return self.display_name or self.name or "Unnamed"


class SearchResultModel(BaseCollibraModel):
    """Model for a single search result."""
    resource: SearchResource
    highlights: Optional[List[SearchHighlight]] = None
    score: Optional[float] = 0.0

    @property
    def id(self) -> str:
        """Convenience accessor for resource.id."""
        return self.resource.id

    @property
    def name(self) -> str:
        """Convenience accessor for resource name."""
        return self.resource.effective_name


# ============================================================================
# Workflow Models
# ============================================================================

class WorkflowDefinitionModel(NamedResource):
    """Collibra Workflow Definition Model."""
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    enabled: bool = False
    start_events: Optional[List[str]] = Field(default=None, alias="startEvents")
    process_id: Optional[str] = Field(default=None, alias="processId")
    guest_user_accessible: Optional[bool] = Field(default=False, alias="guestUserAccessible")
    registered_user_accessible: Optional[bool] = Field(default=False, alias="registeredUserAccessible")
    candidate_user_check_disabled: Optional[bool] = Field(default=False, alias="candidateUserCheckDisabled")
    global_create: Optional[bool] = Field(default=False, alias="globalCreate")
    start_label: Optional[str] = Field(default=None, alias="startLabel")
    domain_type: Optional[ResourceReference] = Field(default=None, alias="domainType")
    asset_type: Optional[ResourceReference] = Field(default=None, alias="assetType")
    community: Optional[ResourceReference] = None
    domain: Optional[ResourceReference] = None
    form_required: Optional[bool] = Field(default=False, alias="formRequired")
    business_item_resource_type: Optional[str] = Field(default=None, alias="businessItemResourceType")
    exclusivity: Optional[str] = None

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)


class WorkflowInstanceModel(BaseCollibraModel):
    """Collibra Workflow Instance Model."""
    id: str
    resource_type: Optional[str] = Field(default=None, alias="resourceType")
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    workflow_definition: Optional[ResourceReference] = Field(default=None, alias="workflowDefinition")
    business_item: Optional[ResourceReference] = Field(default=None, alias="businessItem")
    start_date: Optional[int] = Field(default=None, alias="startDate")
    ended: bool = False
    in_error: bool = Field(default=False, alias="inError")
    sub_process_instances_count: int = Field(default=0, alias="subProcessInstancesCount")

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)


class WorkflowTaskModel(BaseCollibraModel):
    """Collibra Workflow Task Model."""
    id: str
    resource_type: Optional[str] = Field(default=None, alias="resourceType")
    created_on: Optional[int] = Field(default=None, alias="createdOn")
    last_modified_on: Optional[int] = Field(default=None, alias="lastModifiedOn")
    key: Optional[str] = None
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[int] = Field(default=None, alias="dueDate")
    priority: Optional[int] = None
    cancelable: bool = False
    reassignable: bool = False
    form_required: Optional[bool] = Field(default=False, alias="formRequired")
    owner: Optional[ResourceReference] = None
    candidate_users: Optional[List[ResourceReference]] = Field(default=None, alias="candidateUsers")
    workflow_instance: Optional[ResourceReference] = Field(default=None, alias="workflowInstance")
    workflow_definition: Optional[ResourceReference] = Field(default=None, alias="workflowDefinition")
    business_item: Optional[ResourceReference] = Field(default=None, alias="businessItem")

    @property
    def created_datetime(self) -> Optional[datetime]:
        return _get_created_datetime(self)

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        return _get_last_modified_datetime(self)


# ============================================================================
# Paginated Response Model
# ============================================================================

class PaginatedResponseModel(BaseCollibraModel, Generic[T]):
    """
    Generic paginated response model.

    This model wraps API responses that return paginated results,
    providing convenient iteration and pagination helpers.

    Example:
        >>> response = conn.asset.find_assets()
        >>> print(f"Total: {response.total}")
        >>> for asset in response:
        ...     print(asset.name)
        >>> if response.has_more:
        ...     next_page = conn.asset.find_assets(offset=response.next_offset)
    """
    results: List[T] = Field(default_factory=list)
    total: int = 0
    offset: int = 0
    limit: int = 0

    @property
    def has_more(self) -> bool:
        """Check if there are more results available."""
        if self.limit <= 0:
            return False
        return self.offset + self.limit < self.total

    @property
    def next_offset(self) -> int:
        """Get the offset for the next page."""
        return self.offset + len(self.results)

    @property
    def page_count(self) -> int:
        """Get the total number of pages."""
        if self.limit <= 0:
            return 1
        return (self.total + self.limit - 1) // self.limit

    @property
    def current_page(self) -> int:
        """Get the current page number (1-indexed)."""
        if self.limit <= 0:
            return 1
        return (self.offset // self.limit) + 1

    def __len__(self) -> int:
        """Return the number of results in this page."""
        return len(self.results)

    def __iter__(self) -> Iterator[T]:
        """Iterate over results in this page."""
        return iter(self.results)

    def __getitem__(self, index: int) -> T:
        """Get a result by index."""
        return self.results[index]

    def __bool__(self) -> bool:
        """Check if there are any results."""
        return len(self.results) > 0


# ============================================================================
# Full Asset Profile Model
# ============================================================================

class RelationSummary(BaseCollibraModel):
    """Summary of a relation for an asset."""
    id: str
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    target_type: Optional[str] = None
    target_status: Optional[str] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    source_status: Optional[str] = None


class RelationsGrouped(BaseCollibraModel):
    """Relations grouped by direction and type."""
    outgoing: Dict[str, List[RelationSummary]] = Field(default_factory=dict)
    incoming: Dict[str, List[RelationSummary]] = Field(default_factory=dict)
    outgoing_count: int = 0
    incoming_count: int = 0


class ResponsibilitySummary(BaseCollibraModel):
    """Summary of a responsibility assignment."""
    role: str
    owner: str
    owner_id: Optional[str] = None


class AssetProfileModel(BaseCollibraModel):
    """
    Complete asset profile with all related information.

    This model provides a comprehensive view of an asset including
    its attributes, relations, responsibilities, and more.

    Example:
        >>> profile = conn.asset.get_full_profile("uuid")
        >>> print(profile.asset.name)
        >>> print(profile.attributes.get("Description"))
        >>> for rel_type, targets in profile.relations.outgoing.items():
        ...     print(f"{rel_type}: {len(targets)} targets")
    """
    asset: AssetModel
    attributes: Dict[str, Any] = Field(default_factory=dict)
    relations: RelationsGrouped = Field(default_factory=RelationsGrouped)
    responsibilities: List[ResponsibilitySummary] = Field(default_factory=list)
    comments: List[CommentModel] = Field(default_factory=list)
    activities: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def description(self) -> Optional[str]:
        """Get the Description attribute if available."""
        return self.attributes.get("Description")

    @property
    def data_steward(self) -> Optional[str]:
        """Get the Data Steward if assigned."""
        for resp in self.responsibilities:
            if "steward" in resp.role.lower():
                return resp.owner
        return None


# ============================================================================
# Type Aliases for common patterns
# ============================================================================

AssetList = PaginatedResponseModel[AssetModel]
DomainList = PaginatedResponseModel[DomainModel]
CommunityList = PaginatedResponseModel[CommunityModel]
UserList = PaginatedResponseModel[UserModel]
AttributeList = PaginatedResponseModel[AttributeModel]
RelationList = PaginatedResponseModel[RelationModel]
ResponsibilityList = PaginatedResponseModel[ResponsibilityModel]
CommentList = PaginatedResponseModel[CommentModel]
WorkflowDefinitionList = PaginatedResponseModel[WorkflowDefinitionModel]
WorkflowInstanceList = PaginatedResponseModel[WorkflowInstanceModel]
WorkflowTaskList = PaginatedResponseModel[WorkflowTaskModel]
SearchResults = PaginatedResponseModel[SearchResultModel]


# ============================================================================
# Model Factory Functions
# ============================================================================

def parse_asset(data: Dict[str, Any]) -> AssetModel:
    """Parse a dictionary into an AssetModel."""
    return AssetModel.model_validate(data)


def parse_assets(data: Dict[str, Any]) -> AssetList:
    """Parse a paginated response into AssetList."""
    results = [AssetModel.model_validate(item) for item in data.get("results", [])]
    return PaginatedResponseModel[AssetModel](
        results=results,
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 0)
    )


def parse_domain(data: Dict[str, Any]) -> DomainModel:
    """Parse a dictionary into a DomainModel."""
    return DomainModel.model_validate(data)


def parse_domains(data: Dict[str, Any]) -> DomainList:
    """Parse a paginated response into DomainList."""
    results = [DomainModel.model_validate(item) for item in data.get("results", [])]
    return PaginatedResponseModel[DomainModel](
        results=results,
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 0)
    )


def parse_community(data: Dict[str, Any]) -> CommunityModel:
    """Parse a dictionary into a CommunityModel."""
    return CommunityModel.model_validate(data)


def parse_communities(data: Dict[str, Any]) -> CommunityList:
    """Parse a paginated response into CommunityList."""
    results = [CommunityModel.model_validate(item) for item in data.get("results", [])]
    return PaginatedResponseModel[CommunityModel](
        results=results,
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 0)
    )


def parse_user(data: Dict[str, Any]) -> UserModel:
    """Parse a dictionary into a UserModel."""
    return UserModel.model_validate(data)


def parse_users(data: Dict[str, Any]) -> UserList:
    """Parse a paginated response into UserList."""
    results = [UserModel.model_validate(item) for item in data.get("results", [])]
    return PaginatedResponseModel[UserModel](
        results=results,
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 0)
    )


def parse_attribute(data: Dict[str, Any]) -> AttributeModel:
    """Parse a dictionary into an AttributeModel."""
    return AttributeModel.model_validate(data)


def parse_attributes(data: Dict[str, Any]) -> AttributeList:
    """Parse a paginated response into AttributeList."""
    results = [AttributeModel.model_validate(item) for item in data.get("results", [])]
    return PaginatedResponseModel[AttributeModel](
        results=results,
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 0)
    )


def parse_relation(data: Dict[str, Any]) -> RelationModel:
    """Parse a dictionary into a RelationModel."""
    return RelationModel.model_validate(data)


def parse_relations(data: Dict[str, Any]) -> RelationList:
    """Parse a paginated response into RelationList."""
    results = [RelationModel.model_validate(item) for item in data.get("results", [])]
    return PaginatedResponseModel[RelationModel](
        results=results,
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 0)
    )


def parse_responsibility(data: Dict[str, Any]) -> ResponsibilityModel:
    """Parse a dictionary into a ResponsibilityModel."""
    return ResponsibilityModel.model_validate(data)


def parse_responsibilities(data: Dict[str, Any]) -> ResponsibilityList:
    """Parse a paginated response into ResponsibilityList."""
    results = [ResponsibilityModel.model_validate(item) for item in data.get("results", [])]
    return PaginatedResponseModel[ResponsibilityModel](
        results=results,
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 0)
    )


def parse_comment(data: Dict[str, Any]) -> CommentModel:
    """Parse a dictionary into a CommentModel."""
    return CommentModel.model_validate(data)


def parse_comments(data: Dict[str, Any]) -> CommentList:
    """Parse a paginated response into CommentList."""
    results = [CommentModel.model_validate(item) for item in data.get("results", [])]
    return PaginatedResponseModel[CommentModel](
        results=results,
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 0)
    )


def parse_workflow_definition(data: Dict[str, Any]) -> WorkflowDefinitionModel:
    """Parse a dictionary into a WorkflowDefinitionModel."""
    return WorkflowDefinitionModel.model_validate(data)


def parse_workflow_definitions(data: Dict[str, Any]) -> WorkflowDefinitionList:
    """Parse a paginated response into WorkflowDefinitionList."""
    results = [WorkflowDefinitionModel.model_validate(item) for item in data.get("results", [])]
    return PaginatedResponseModel[WorkflowDefinitionModel](
        results=results,
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 0)
    )


def parse_workflow_instance(data: Dict[str, Any]) -> WorkflowInstanceModel:
    """Parse a dictionary into a WorkflowInstanceModel."""
    return WorkflowInstanceModel.model_validate(data)


def parse_workflow_instances(data: Dict[str, Any]) -> WorkflowInstanceList:
    """Parse a paginated response into WorkflowInstanceList."""
    results = [WorkflowInstanceModel.model_validate(item) for item in data.get("results", [])]
    return PaginatedResponseModel[WorkflowInstanceModel](
        results=results,
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 0)
    )


def parse_workflow_task(data: Dict[str, Any]) -> WorkflowTaskModel:
    """Parse a dictionary into a WorkflowTaskModel."""
    return WorkflowTaskModel.model_validate(data)


def parse_workflow_tasks(data: Dict[str, Any]) -> WorkflowTaskList:
    """Parse a paginated response into WorkflowTaskList."""
    results = [WorkflowTaskModel.model_validate(item) for item in data.get("results", [])]
    return PaginatedResponseModel[WorkflowTaskModel](
        results=results,
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 0)
    )


def parse_search_results(data: Dict[str, Any]) -> SearchResults:
    """Parse a paginated response into SearchResults."""
    results = [SearchResultModel.model_validate(item) for item in data.get("results", [])]
    return PaginatedResponseModel[SearchResultModel](
        results=results,
        total=data.get("total", 0),
        offset=data.get("offset", 0),
        limit=data.get("limit", 0)
    )
