# ============================================================
# AETHER LINK - REVIEW MODEL
# ============================================================
# Purpose: Course reviews and ratings with helpful votes
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, DECIMAL, Index, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class ReviewStatus(str, enum.Enum):
    """Review status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    HIDDEN = "hidden"
    DELETED = "deleted"


class ReviewType(str, enum.Enum):
    """Review type enumeration."""
    COURSE = "course"
    TEACHER = "teacher"
    INSTITUTION = "institution"


# ============================================================
# 1. REVIEW MODEL
# ============================================================

class Review(Base):
    __tablename__ = "reviews"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # NEW: Optional teacher review
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # RATING ⭐ (1-5)
    # ============================================================
    rating = Column(Integer, nullable=False)
    
    # NEW: Breakdown ratings
    rating_teaching = Column(Integer, nullable=True)  # 1-5
    rating_content = Column(Integer, nullable=True)   # 1-5
    rating_support = Column(Integer, nullable=True)   # 1-5
    rating_value = Column(Integer, nullable=True)     # 1-5
    
    # ============================================================
    # REVIEW CONTENT
    # ============================================================
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    
    # NEW: Pros and Cons
    pros = Column(Text, nullable=True)
    cons = Column(Text, nullable=True)
    
    # NEW: Would recommend
    would_recommend = Column(Boolean, default=True, nullable=False)
    
    # ============================================================
    # REVIEW TYPE
    # ============================================================
    review_type = Column(
        String(50),
        default=ReviewType.COURSE.value,
        nullable=False
    )
    
    # ============================================================
    # VERIFICATION ⭐ (Verified purchase)
    # ============================================================
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # NEW: Verification method
    verification_method = Column(String(50), nullable=True)  # enrollment, manual
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=ReviewStatus.PENDING.value,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # HELPFUL VOTES
    # ============================================================
    helpful_count = Column(Integer, default=0, nullable=False)
    not_helpful_count = Column(Integer, default=0, nullable=False)
    
    # ============================================================
    # NEW: FLAG TRACKING
    # ============================================================
    flag_count = Column(Integer, default=0, nullable=False)
    flagged_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # NEW: RESPONSE (Teacher/Admin response)
    # ============================================================
    response = Column(Text, nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    responded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # NEW: ANONYMOUS
    # ============================================================
    is_anonymous = Column(Boolean, default=False, nullable=False)
    
    # ============================================================
    # NEW: METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_reviews_course_student', 'course_id', 'student_id', unique=True),
        Index('ix_reviews_course_rating', 'course_id', 'rating'),
        Index('ix_reviews_student', 'student_id'),
        Index('ix_reviews_status', 'status'),
        Index('ix_reviews_verified', 'is_verified'),
        Index('ix_reviews_created', 'created_at'),
        Index('ix_reviews_helpful', 'helpful_count'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course = relationship(
        "Course",
        back_populates="reviews",
        foreign_keys=[course_id]
    )
    
    student = relationship(
        "User",
        back_populates="reviews",
        foreign_keys=[student_id]
    )
    
    # NEW: Teacher relationship
    teacher = relationship(
        "User",
        foreign_keys=[teacher_id],
        uselist=False
    )
    
    verified_by_user = relationship(
        "User",
        foreign_keys=[verified_by],
        uselist=False
    )
    
    responded_by_user = relationship(
        "User",
        foreign_keys=[responded_by],
        uselist=False
    )
    
    helpful_votes = relationship(
        "ReviewHelpfulVote",
        back_populates="review",
        cascade="all, delete-orphan"
    )
    
    # NEW: Review flags
    flags = relationship(
        "ReviewFlag",
        back_populates="review",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Review {self.id}: {self.rating}⭐ - {self.course.title if self.course else 'Unknown'}>"
    
    def __str__(self) -> str:
        return f"{self.rating}⭐ - {self.title or 'No title'}"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_approved(self) -> bool:
        """Check if review is approved."""
        return self.status == ReviewStatus.APPROVED.value
    
    @property
    def is_pending_review(self) -> bool:
        """Check if review is pending."""
        return self.status == ReviewStatus.PENDING.value
    
    @property
    def is_rejected(self) -> bool:
        """Check if review is rejected."""
        return self.status == ReviewStatus.REJECTED.value
    
    @property
    def is_flagged_review(self) -> bool:
        """Check if review is flagged."""
        return self.status == ReviewStatus.FLAGGED.value or self.flag_count > 0
    
    @property
    def is_hidden_review(self) -> bool:
        """Check if review is hidden."""
        return self.status == ReviewStatus.HIDDEN.value
    
    @property
    def is_deleted_review(self) -> bool:
        """Check if review is deleted."""
        return self.status == ReviewStatus.DELETED.value
    
    @property
    def is_verified_purchase(self) -> bool:
        """Check if review is verified."""
        return self.is_verified
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        status_map = {
            "pending": "⏳ Pending",
            "approved": "✅ Approved",
            "rejected": "❌ Rejected",
            "flagged": "🚩 Flagged",
            "hidden": "👻 Hidden",
            "deleted": "🗑️ Deleted",
        }
        return status_map.get(self.status, "Unknown")
    
    @property
    def rating_display(self) -> str:
        """Get star rating display."""
        return "⭐" * self.rating + "☆" * (5 - self.rating)
    
    @property
    def helpful_percentage(self) -> float:
        """Calculate helpful percentage."""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0.0
        return (self.helpful_count / total) * 100
    
    @property
    def is_high_rated(self) -> bool:
        """Check if rating is high (4-5)."""
        return self.rating >= 4
    
    @property
    def is_low_rated(self) -> bool:
        """Check if rating is low (1-2)."""
        return self.rating <= 2
    
    @property
    def has_response(self) -> bool:
        """Check if review has a response."""
        return self.response is not None
    
    @property
    def display_name(self) -> str:
        """Get display name (anonymous or real name)."""
        if self.is_anonymous:
            return "Anonymous Student"
        return self.student.full_name if self.student else "Unknown Student"
    
    @property
    def average_breakdown(self) -> dict:
        """Get average of breakdown ratings."""
        ratings = [
            self.rating_teaching,
            self.rating_content,
            self.rating_support,
            self.rating_value,
        ]
        valid_ratings = [r for r in ratings if r is not None]
        if not valid_ratings:
            return {}
        return {
            "average": sum(valid_ratings) / len(valid_ratings),
            "teaching": self.rating_teaching,
            "content": self.rating_content,
            "support": self.rating_support,
            "value": self.rating_value,
        }
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def approve(self, verified_by: int = None) -> None:
        """Approve the review."""
        self.status = ReviewStatus.APPROVED.value
        if verified_by:
            self.verified_by = verified_by
            self.verified_at = func.now()
            self.is_verified = True
    
    def reject(self, reason: str = None) -> None:
        """Reject the review."""
        self.status = ReviewStatus.REJECTED.value
        if reason:
            if self.metadata is None:
                self.metadata = {}
            self.metadata["rejection_reason"] = reason
    
    def flag(self) -> None:
        """Flag the review for moderation."""
        self.flag_count += 1
        self.flagged_at = func.now()
        if self.flag_count >= 3:
            self.status = ReviewStatus.FLAGGED.value
    
    def hide(self) -> None:
        """Hide the review."""
        self.status = ReviewStatus.HIDDEN.value
    
    def unhide(self) -> None:
        """Unhide the review."""
        self.status = ReviewStatus.APPROVED.value
    
    def soft_delete_review(self) -> None:
        """Soft delete the review."""
        self.status = ReviewStatus.DELETED.value
        self.deleted_at = func.now()
    
    def restore_review(self) -> None:
        """Restore a soft-deleted review."""
        self.status = ReviewStatus.APPROVED.value
        self.deleted_at = None
    
    def verify(self, method: str = "enrollment", verified_by: int = None) -> None:
        """Mark review as verified purchase."""
        self.is_verified = True
        self.verified_at = func.now()
        self.verification_method = method
        if verified_by:
            self.verified_by = verified_by
    
    def unverify(self) -> None:
        """Unmark review as verified."""
        self.is_verified = False
        self.verified_at = None
        self.verification_method = None
        self.verified_by = None
    
    def add_response(self, response: str, responded_by: int) -> None:
        """Add teacher/admin response to review."""
        self.response = response
        self.responded_at = func.now()
        self.responded_by = responded_by
    
    def edit_response(self, response: str) -> None:
        """Edit response."""
        self.response = response
        self.updated_at = func.now()
    
    def increment_helpful(self) -> None:
        """Increment helpful count."""
        self.helpful_count += 1
    
    def increment_not_helpful(self) -> None:
        """Increment not helpful count."""
        self.not_helpful_count += 1
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    @staticmethod
    def validate_rating(rating: int) -> bool:
        """Validate rating is between 1-5."""
        return 1 <= rating <= 5
    
    @staticmethod
    def validate_title(title: str) -> bool:
        """Validate title length."""
        if not title:
            return True
        return 3 <= len(title) <= 255
    
    @staticmethod
    def validate_content(content: str) -> bool:
        """Validate content length."""
        if not content:
            return True
        return 10 <= len(content) <= 5000
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert review to dictionary."""
        data = {
            "id": self.id,
            "course_id": self.course_id,
            "course_title": self.course.title if self.course else None,
            "student_id": self.student_id,
            "student_name": self.display_name,
            "is_anonymous": self.is_anonymous,
            "rating": self.rating,
            "rating_display": self.rating_display,
            "rating_teaching": self.rating_teaching,
            "rating_content": self.rating_content,
            "rating_support": self.rating_support,
            "rating_value": self.rating_value,
            "breakdown": self.average_breakdown,
            "title": self.title,
            "content": self.content,
            "pros": self.pros,
            "cons": self.cons,
            "would_recommend": self.would_recommend,
            "is_verified": self.is_verified,
            "is_approved": self.is_approved,
            "status": self.status,
            "display_status": self.display_status,
            "helpful_count": self.helpful_count,
            "not_helpful_count": self.not_helpful_count,
            "helpful_percentage": self.helpful_percentage,
            "has_response": self.has_response,
            "response": self.response,
            "response_responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "status": self.status,
                "verified_at": self.verified_at.isoformat() if self.verified_at else None,
                "verified_by": self.verified_by,
                "verification_method": self.verification_method,
                "flag_count": self.flag_count,
                "flagged_at": self.flagged_at.isoformat() if self.flagged_at else None,
                "responded_by": self.responded_by,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing review data."""
        data = self.to_dict()
        # Remove sensitive fields
        data.pop("is_anonymous", None)
        data.pop("student_id", None)
        data.pop("student_name", None)
        # Only show response if review is approved
        if not self.is_approved:
            data.pop("response", None)
            data.pop("has_response", None)
        return data
    
    def to_student_json(self) -> dict:
        """Student-facing review data."""
        data = self.to_dict()
        data.pop("metadata", None)
        return data


# ============================================================
# 2. REVIEW HELPFUL VOTE MODEL
# ============================================================

class ReviewHelpfulVote(Base):
    __tablename__ = "review_helpful_votes"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # VOTE TYPE
    # ============================================================
    is_helpful = Column(Boolean, default=True, nullable=False)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_review_votes_unique', 'review_id', 'user_id', unique=True),
        Index('ix_review_votes_review', 'review_id'),
        Index('ix_review_votes_user', 'user_id'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    review = relationship(
        "Review",
        back_populates="helpful_votes",
        foreign_keys=[review_id]
    )
    
    user = relationship(
        "User",
        back_populates="review_helpful_votes",
        foreign_keys=[user_id]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<ReviewHelpfulVote {self.id}: {self.user_id} -> {self.review_id}>"


# ============================================================
# 3. REVIEW FLAG MODEL
# ============================================================

class ReviewFlag(Base):
    """Flag inappropriate reviews for moderation."""
    __tablename__ = "review_flags"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    flagged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    reason = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, reviewed, dismissed, actioned
    
    # Review tracking
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    review = relationship("Review", back_populates="flags")
    flagger = relationship("User", foreign_keys=[flagged_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    __table_args__ = (
        Index('ix_review_flags_review', 'review_id'),
        Index('ix_review_flags_status', 'status'),
        Index('ix_review_flags_created', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ReviewFlag {self.id}: {self.reason}>"
    
    def review(self, reviewed_by: int, notes: str = None) -> None:
        """Mark flag as reviewed."""
        self.status = "reviewed"
        self.reviewed_by = reviewed_by
        self.reviewed_at = func.now()
        if notes:
            self.review_notes = notes
    
    def dismiss(self, reviewed_by: int, notes: str = None) -> None:
        """Dismiss flag (no action needed)."""
        self.status = "dismissed"
        self.reviewed_by = reviewed_by
        self.reviewed_at = func.now()
        if notes:
            self.review_notes = notes
    
    def action(self, reviewed_by: int, notes: str = None) -> None:
        """Action the flag (hide/delete content)."""
        self.status = "actioned"
        self.reviewed_by = reviewed_by
        self.reviewed_at = func.now()
        if notes:
            self.review_notes = notes


# ============================================================
# 4. COURSE STATS (Aggregated review data)
# ============================================================

class CourseReviewStats(Base):
    """Aggregated course review statistics."""
    __tablename__ = "course_review_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Review counts
    total_reviews = Column(Integer, default=0, nullable=False)
    verified_reviews = Column(Integer, default=0, nullable=False)
    
    # Average ratings
    avg_rating = Column(DECIMAL(3, 2), default=0.00, nullable=False)
    avg_teaching = Column(DECIMAL(3, 2), nullable=True)
    avg_content = Column(DECIMAL(3, 2), nullable=True)
    avg_support = Column(DECIMAL(3, 2), nullable=True)
    avg_value = Column(DECIMAL(3, 2), nullable=True)
    
    # Rating distribution
    rating_5_count = Column(Integer, default=0, nullable=False)
    rating_4_count = Column(Integer, default=0, nullable=False)
    rating_3_count = Column(Integer, default=0, nullable=False)
    rating_2_count = Column(Integer, default=0, nullable=False)
    rating_1_count = Column(Integer, default=0, nullable=False)
    
    # Recommendation rate
    recommend_count = Column(Integer, default=0, nullable=False)
    not_recommend_count = Column(Integer, default=0, nullable=False)
    recommend_rate = Column(DECIMAL(5, 2), default=0.00, nullable=False)
    
    # Timestamps
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    course = relationship("Course", foreign_keys=[course_id])
    
    def __repr__(self) -> str:
        return f"<CourseReviewStats {self.course_id}: {self.avg_rating}⭐>"
    
    @property
    def rating_distribution(self) -> dict:
        """Get rating distribution."""
        return {
            5: self.rating_5_count,
            4: self.rating_4_count,
            3: self.rating_3_count,
            2: self.rating_2_count,
            1: self.rating_1_count,
        }
    
    @property
    def total_votes(self) -> int:
        """Get total votes (helpful + not helpful)."""
        # This would need to be calculated from reviews
        return 0  # Placeholder