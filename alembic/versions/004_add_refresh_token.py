"""Add refresh token columns to users table

Revision ID: 004
Revises: 003
Create Date: 2026-03-07

EXPLAINING THE CHANGE:
======================
WHAT:
  Thêm 2 cột vào bảng `users`:
    - refresh_token_hash  : SHA-256 hash của refresh token (không lưu raw token!)
    - refresh_token_expires_at : thời điểm refresh token hết hạn (UTC)

WHY (Kiến thức bảo mật quan trọng):
  Trước đây app chỉ có Access Token (JWT, 30 phút).
  Khi hết hạn → user bị văng ra ngoài dù đang làm việc bình thường.
  
  Giải pháp: thêm Refresh Token (7 ngày).
    - Access token: ngắn hạn, stateless (server không cần lưu)
    - Refresh token: dài hạn, stateful (server lưu hash trong DB để có thể thu hồi)

WHY STORE HASH (not raw token)?
  Nếu database bị tấn công (SQL Injection, breach...):
    - Raw token → kẻ tấn công có thể dùng ngay để lấy access token mới
    - Hashed token → vô dụng, không thể reverse được
  
  Dùng SHA-256 (không phải bcrypt) vì:
    - Refresh token đã có entropy cao (64 bytes random) → không cần slow hash
    - bcrypt chỉ cần cho passwords (user-chosen, entropy thấp)

NULLABLE:
  Cả 2 cột đều nullable=True vì:
    - User mới tạo chưa login → chưa có refresh token
    - Sau logout → xóa giá trị (= NULL) để vô hiệu hóa session
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Thêm cột refresh_token_hash:
    #   - String(64) vì SHA-256 hex digest luôn là 64 ký tự
    #   - index=True để tìm kiếm nhanh khi client gửi refresh token lên
    op.add_column(
        'users',
        sa.Column('refresh_token_hash', sa.String(length=64), nullable=True)
    )
    op.create_index(
        op.f('ix_users_refresh_token_hash'),
        'users',
        ['refresh_token_hash'],
        unique=False
    )

    # Thêm cột refresh_token_expires_at:
    #   - DateTime(timezone=True) để lưu UTC timestamp
    #   - Server so sánh với datetime.now(UTC) để kiểm tra hết hạn
    op.add_column(
        'users',
        sa.Column(
            'refresh_token_expires_at',
            sa.DateTime(timezone=True),
            nullable=True
        )
    )


def downgrade() -> None:
    # Xóa index trước, rồi mới xóa cột (đúng thứ tự)
    op.drop_index(op.f('ix_users_refresh_token_hash'), table_name='users')
    op.drop_column('users', 'refresh_token_hash')
    op.drop_column('users', 'refresh_token_expires_at')
