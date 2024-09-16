# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from datetime import date
from datetime import datetime
from typing import Optional
from typing import Set
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pydantic import Extra
from pydantic import ValidationError
from pydantic import validator


class OrgUnit(BaseModel):
    """API model for os2sync

    https://www.os2sync.dk/downloads/API%20Documentation.pdf

    public string ShortKey;
    public string Name;
    public string ParentOrgUnitUuid;
    public string PayoutUnitUuid;
    public string ManagerUuid;
    public DateTime Timestamp;
    public string PhoneNumber;
    public string Email;
    public string Location;
    public string LOSShortName;
    public string LOSId;
    public string DtrId;
    public string ContactOpenHours;
    public string EmailRemarks;
    public string Contact;
    public string PostReturn;
    public string PhoneOpenHours;
    public string Ean;
    public string Url;
    public string Landline;
    public string Post;
    public string FOA;
    public string PNR;
    public string SOR;
    public OrgUnitType Type;
    public List<string> Tasks;
    public List<string> ItSystems;
    public List<string> ContactForTasks;
    """

    class Config:
        extra = Extra.forbid

    def json(self):
        return jsonable_encoder(self.dict())

    Uuid: UUID
    ShortKey: Optional[str] = None
    Name: Optional[str]
    ParentOrgUnitUuid: Optional[UUID]
    PayoutUnitUuid: Optional[UUID] = None
    ManagerUuid: Optional[UUID] = None
    PhoneNumber: Optional[str] = None
    Email: Optional[str] = None
    Location: Optional[str] = None
    LOSShortName: Optional[str] = None
    LOSId: Optional[str] = None
    DtrId: Optional[str] = None
    ContactOpenHours: Optional[str] = None
    EmailRemarks: Optional[str] = None
    Contact: Optional[str] = None
    PostReturn: Optional[str] = None
    PhoneOpenHours: Optional[str] = None
    Ean: Optional[str] = None
    Url: Optional[str] = None
    Landline: Optional[str] = None
    Post: Optional[str] = None
    PostSecondary: Optional[str] = None
    FOA: Optional[str] = None
    PNR: Optional[str] = None
    SOR: Optional[str] = None
    Tasks: Set[UUID] = set()
    ItSystems: Set[UUID] = set()
    ContactForTasks: Set[UUID] = set()
    ContactPlaces: Set[UUID] = set()


# User:
"""
    public class UserRegistration {
        public string Uuid;
        public string ShortKey;
        public string UserId;
        public string PhoneNumber;
        public string Landline;
        public string Email;
        public string RacfID;
        public string Location;
        public string FMKID;
        public List<Position> Positions;
        public Person Person;
        public DateTime Timestamp;
    }

    public class Position {
        public string Name;
        public string OrgUnitUuid;
        public string StartDate; // yyyy-MM-dd (or null)
        public string StopDate; // yyyy-MM-dd (or null)
    }
    public class Person {
        public string Name;
        public string Cpr;
    }
    """


class Person(BaseModel):
    Name: str
    Cpr: str | None = None


class Position(BaseModel):
    Name: str  # Job-function
    OrgUnitUuid: UUID
    # Not in use yet so always None:
    StartDate: date | None = None
    StopDate: date | None = None


class User(BaseModel):
    Uuid: UUID
    ShortKey: str | None = None  # Not in use yet so always None:
    UserId: str  # Username

    Person: Person
    Positions: list[Position]
    PhoneNumber: str | None
    Landline: str | None
    Email: str | None
    RacfID: str | None
    Location: str | None
    FMKID: str | None

    DateTime: datetime | None = None  # Registration time for os2sync - never set this

    @validator("Positions")
    def has_positions(cls, v):
        """A user must have at least one engagement in os2sync"""
        if len(v) < 1:
            raise ValidationError
        return v
