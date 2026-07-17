from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import String, Integer, Date, DateTime, Numeric, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Series(Base):
    __tablename__ = "series"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    series_type: Mapped[Optional[str]] = mapped_column(String(100))

    matches: Mapped[List["Match"]] = relationship("Match", back_populates="series")

    def __repr__(self) -> str:
        return f"<Series(id={self.id}, name='{self.name}')>"

class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    capacity: Mapped[Optional[int]] = mapped_column(Integer)

    matches: Mapped[List["Match"]] = relationship("Match", back_populates="venue")

    def __repr__(self) -> str:
        return f"<Venue(id={self.id}, name='{self.name}')>"

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[Optional[str]] = mapped_column(String(50))

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name='{self.name}')>"

class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(100))
    batting_style: Mapped[Optional[str]] = mapped_column(String(100))
    bowling_style: Mapped[Optional[str]] = mapped_column(String(100))
    image_url: Mapped[Optional[str]] = mapped_column(String)

    def __repr__(self) -> str:
        return f"<Player(id={self.id}, name='{self.name}')>"

class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_id: Mapped[Optional[int]] = mapped_column(ForeignKey("series.id", ondelete="SET NULL"))
    venue_id: Mapped[Optional[int]] = mapped_column(ForeignKey("venues.id", ondelete="SET NULL"))
    match_desc: Mapped[Optional[str]] = mapped_column(String(255))
    format: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[Optional[str]] = mapped_column(String(255))
    team1_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    team2_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    toss_winner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"))
    toss_decision: Mapped[Optional[str]] = mapped_column(String(50))
    winner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"))
    match_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_live: Mapped[bool] = mapped_column(Boolean, default=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=True)
    match_overs_limit: Mapped[Optional[int]] = mapped_column(Integer, default=20)
    player_of_the_match_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))

    series: Mapped[Optional["Series"]] = relationship("Series", back_populates="matches")
    venue: Mapped[Optional["Venue"]] = relationship("Venue", back_populates="matches")

    team1: Mapped["Team"] = relationship("Team", foreign_keys=[team1_id])
    team2: Mapped["Team"] = relationship("Team", foreign_keys=[team2_id])
    toss_winner: Mapped[Optional["Team"]] = relationship("Team", foreign_keys=[toss_winner_id])
    winner: Mapped[Optional["Team"]] = relationship("Team", foreign_keys=[winner_id])
    player_of_the_match: Mapped[Optional["Player"]] = relationship("Player", foreign_keys=[player_of_the_match_id])

    innings: Mapped[List["Innings"]] = relationship("Innings", back_populates="match", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Match(id={self.id}, desc='{self.match_desc}', format='{self.format}', is_live={self.is_live})>"

class Innings(Base):
    __tablename__ = "innings"
    __table_args__ = (UniqueConstraint("match_id", "innings_num", name="unique_match_innings"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    innings_num: Mapped[int] = mapped_column(Integer, nullable=False)
    batting_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    bowling_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    runs: Mapped[int] = mapped_column(Integer, default=0)
    wickets: Mapped[int] = mapped_column(Integer, default=0)
    overs: Mapped[float] = mapped_column(Numeric(4, 1), default=0.0)
    extras: Mapped[int] = mapped_column(Integer, default=0)
    wides: Mapped[int] = mapped_column(Integer, default=0)
    no_balls: Mapped[int] = mapped_column(Integer, default=0)
    byes: Mapped[int] = mapped_column(Integer, default=0)
    leg_byes: Mapped[int] = mapped_column(Integer, default=0)

    match: Mapped["Match"] = relationship("Match", back_populates="innings")
    batting_team: Mapped["Team"] = relationship("Team", foreign_keys=[batting_team_id])
    bowling_team: Mapped["Team"] = relationship("Team", foreign_keys=[bowling_team_id])

    batting_scores: Mapped[List["BattingScore"]] = relationship("BattingScore", back_populates="innings", cascade="all, delete-orphan")
    bowling_scores: Mapped[List["BowlingScore"]] = relationship("BowlingScore", back_populates="innings", cascade="all, delete-orphan")
    fielding_records: Mapped[List["FieldingRecord"]] = relationship("FieldingRecord", back_populates="innings", cascade="all, delete-orphan")
    partnerships: Mapped[List["Partnership"]] = relationship("Partnership", back_populates="innings", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Innings(id={self.id}, match_id={self.match_id}, num={self.innings_num}, score={self.runs}/{self.wickets})>"

class BattingScore(Base):
    __tablename__ = "batting_scores"
    __table_args__ = (UniqueConstraint("innings_id", "player_id", name="unique_innings_batsman"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    innings_id: Mapped[int] = mapped_column(ForeignKey("innings.id", ondelete="CASCADE"))
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    runs: Mapped[int] = mapped_column(Integer, default=0)
    balls: Mapped[int] = mapped_column(Integer, default=0)
    fours: Mapped[int] = mapped_column(Integer, default=0)
    sixes: Mapped[int] = mapped_column(Integer, default=0)
    strike_rate: Mapped[float] = mapped_column(Numeric(6, 2), default=0.0)
    out: Mapped[bool] = mapped_column(Boolean, default=True)
    dismissal_type: Mapped[Optional[str]] = mapped_column(String(50))
    dismissal_text: Mapped[Optional[str]] = mapped_column(String)
    bowler_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    fielder_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))

    innings: Mapped["Innings"] = relationship("Innings", back_populates="batting_scores")
    player: Mapped["Player"] = relationship("Player", foreign_keys=[player_id])
    bowler: Mapped[Optional["Player"]] = relationship("Player", foreign_keys=[bowler_id])
    fielder: Mapped[Optional["Player"]] = relationship("Player", foreign_keys=[fielder_id])

    def __repr__(self) -> str:
        return f"<BattingScore(player_id={self.player_id}, runs={self.runs}, balls={self.balls})>"

class BowlingScore(Base):
    __tablename__ = "bowling_scores"
    __table_args__ = (UniqueConstraint("innings_id", "player_id", name="unique_innings_bowler"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    innings_id: Mapped[int] = mapped_column(ForeignKey("innings.id", ondelete="CASCADE"))
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    overs: Mapped[float] = mapped_column(Numeric(4, 1), default=0.0)
    maidens: Mapped[int] = mapped_column(Integer, default=0)
    runs_conceded: Mapped[int] = mapped_column(Integer, default=0)
    wickets: Mapped[int] = mapped_column(Integer, default=0)
    economy: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)

    innings: Mapped["Innings"] = relationship("Innings", back_populates="bowling_scores")
    player: Mapped["Player"] = relationship("Player")

    def __repr__(self) -> str:
        return f"<BowlingScore(player_id={self.player_id}, wickets={self.wickets}, runs={self.runs_conceded})>"

class FieldingRecord(Base):
    __tablename__ = "fielding_records"
    __table_args__ = (UniqueConstraint("innings_id", "player_id", name="unique_innings_fielder"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    innings_id: Mapped[int] = mapped_column(ForeignKey("innings.id", ondelete="CASCADE"))
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    catches: Mapped[int] = mapped_column(Integer, default=0)
    stumpings: Mapped[int] = mapped_column(Integer, default=0)
    run_outs: Mapped[int] = mapped_column(Integer, default=0)

    innings: Mapped["Innings"] = relationship("Innings", back_populates="fielding_records")
    player: Mapped["Player"] = relationship("Player")

    def __repr__(self) -> str:
        return f"<FieldingRecord(player_id={self.player_id}, catches={self.catches}, stumpings={self.stumpings})>"

class Partnership(Base):
    __tablename__ = "partnerships"
    __table_args__ = (UniqueConstraint("innings_id", "batsman1_id", "batsman2_id", name="unique_partnership"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    innings_id: Mapped[int] = mapped_column(ForeignKey("innings.id", ondelete="CASCADE"))
    batsman1_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    batsman2_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    runs: Mapped[int] = mapped_column(Integer, default=0)
    balls: Mapped[int] = mapped_column(Integer, default=0)
    boundaries_fours: Mapped[int] = mapped_column(Integer, default=0)
    boundaries_sixes: Mapped[int] = mapped_column(Integer, default=0)
    unbroken: Mapped[bool] = mapped_column(Boolean, default=False)

    innings: Mapped["Innings"] = relationship("Innings", back_populates="partnerships")
    batsman1: Mapped["Player"] = relationship("Player", foreign_keys=[batsman1_id])
    batsman2: Mapped["Player"] = relationship("Player", foreign_keys=[batsman2_id])

    def __repr__(self) -> str:
        return f"<Partnership(batsman1_id={self.batsman1_id}, batsman2_id={self.batsman2_id}, runs={self.runs})>"
