from typing import Dict, Any


class User:

    def __init__(self,
                 user_id: int,
                 mode: str = ''):

        self._user_id: int = user_id

        self._mode: str = mode


    # --- Геттеры ---
    def get_user_id(self) -> int:
        return self._user_id

    def get_mode(self) -> str:
        return self._mode



    def set_mode(self, value: str):
        self._mode = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self._user_id,
            'mode': self._mode
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        user = cls(
            user_id=data['user_id'],
            mode=data.get('mode', '')
        )
        return user

    def __repr__(self) -> str:
        return f"User(id={self._user_id})"

    def __eq__(self, other) -> bool:
        return isinstance(other, User) and self._user_id == other._user_id

    def __hash__(self) -> int:
        return hash(self._user_id)