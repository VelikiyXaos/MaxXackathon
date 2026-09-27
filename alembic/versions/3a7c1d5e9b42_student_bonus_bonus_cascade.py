"""student_bonus: ON DELETE CASCADE для bonus_id

Revision ID: 3a7c1d5e9b42
Revises: b511b9409203
Create Date: 2026-09-26 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '3a7c1d5e9b42'
down_revision: Union[str, None] = 'b511b9409203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Удаление бонуса само удаляет все выдачи студентам."""
    op.drop_constraint(
        'student_bonus_bonus_id_fkey', 'student_bonus', type_='foreignkey'
    )
    op.create_foreign_key(
        'student_bonus_bonus_id_fkey',
        'student_bonus',
        'bonus',
        ['bonus_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    """Возврат к удалению ссылок вручную (ON DELETE NO ACTION)."""
    op.drop_constraint(
        'student_bonus_bonus_id_fkey', 'student_bonus', type_='foreignkey'
    )
    op.create_foreign_key(
        'student_bonus_bonus_id_fkey',
        'student_bonus',
        'bonus',
        ['bonus_id'],
        ['id'],
    )
