from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=False)
    interests = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)

    age_min = Column(Integer, default=18)  # Пример: 18 лет
    age_max = Column(Integer, default=99)
    city_filter = Column(String)

    liked_users = relationship(
        "UserLike",
        foreign_keys="[UserLike.liker_id]",
        back_populates="liker",
        cascade="all, delete-orphan"
    )

    liked_by_users = relationship(
        "UserLike",
        foreign_keys="[UserLike.liked_id]",
        back_populates="liked",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<UserProfile(telegram_id={self.telegram_id}, "
            f"name={self.name}, age={self.age}, city={self.city})>"
        )




class UserLike(Base):
    __tablename__ = "user_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    liker_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"))
    liked_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"))

    liker = relationship("UserProfile", foreign_keys=[liker_id], back_populates="liked_users")
    liked = relationship("UserProfile", foreign_keys=[liked_id], back_populates="liked_by_users")

    def __repr__(self):
        return f"<UserLike(liker_id={self.liker_id}, liked_id={self.liked_id})>"
    



