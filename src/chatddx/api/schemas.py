from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict

from chatddx.identity import Person, Role


class _Schema(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")


class SignIn(_Schema):
    login: str
    password: str


class Me(_Schema):
    id: int
    login: str
    name: str
    roles: list[Role]

    @classmethod
    def of(cls, person: Person) -> Self:
        return cls(
            id=person.id,
            login=person.login,
            name=person.name,
            roles=sorted(person.roles),
        )


class SignedIn(_Schema):
    token: str
    person: Me
