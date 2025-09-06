"""Tests for data models."""

import pytest
from kaggle_discussion_extractor.core.models import Author, Reply, Discussion
from datetime import datetime


class TestAuthor:
    """Test Author model."""
    
    def test_author_creation(self):
        """Test creating an Author instance."""
        author = Author(
            name="John Doe",
            username="johndoe",
            rank="5th in this Competition",
            badges=["Competition Host", "Expert"],
            profile_url="https://www.kaggle.com/johndoe"
        )
        
        assert author.name == "John Doe"
        assert author.username == "johndoe"
        assert author.rank == "5th in this Competition"
        assert len(author.badges) == 2
        assert "Competition Host" in author.badges
    
    def test_author_to_dict(self):
        """Test converting Author to dictionary."""
        author = Author(name="Jane Smith", username="janesmith")
        author_dict = author.to_dict()
        
        assert author_dict["name"] == "Jane Smith"
        assert author_dict["username"] == "janesmith"
        assert author_dict["badges"] == []
    
    def test_author_string_representation(self):
        """Test string representation of Author."""
        author = Author(
            name="Bob Johnson",
            username="bobjohnson",
            badges=["Expert"],
            rank="10th in this Competition"
        )
        
        str_repr = str(author)
        assert "Bob Johnson" in str_repr
        assert "@bobjohnson" in str_repr
        assert "Expert" in str_repr
        assert "10th in this Competition" in str_repr


class TestReply:
    """Test Reply model."""
    
    def test_reply_creation(self):
        """Test creating a Reply instance."""
        author = Author(name="Test User", username="testuser")
        reply = Reply(
            reply_number="1",
            content="This is a test reply",
            author=author,
            upvotes=5,
            timestamp="2024-01-15 10:30:00",
            depth=0
        )
        
        assert reply.reply_number == "1"
        assert reply.content == "This is a test reply"
        assert reply.author.username == "testuser"
        assert reply.upvotes == 5
        assert reply.depth == 0
        assert len(reply.sub_replies) == 0
    
    def test_reply_with_sub_replies(self):
        """Test Reply with nested sub-replies."""
        main_author = Author(name="Main", username="main")
        sub_author = Author(name="Sub", username="sub")
        
        sub_reply = Reply(
            reply_number="1.1",
            content="Sub reply",
            author=sub_author,
            upvotes=2,
            timestamp="2024-01-15 11:00:00",
            depth=1
        )
        
        main_reply = Reply(
            reply_number="1",
            content="Main reply",
            author=main_author,
            upvotes=10,
            timestamp="2024-01-15 10:30:00",
            depth=0,
            sub_replies=[sub_reply]
        )
        
        assert len(main_reply.sub_replies) == 1
        assert main_reply.sub_replies[0].reply_number == "1.1"
        assert main_reply.count_all_replies() == 1
    
    def test_reply_to_dict(self):
        """Test converting Reply to dictionary."""
        author = Author(name="Test", username="test")
        reply = Reply(
            reply_number="1",
            content="Test content",
            author=author,
            upvotes=3,
            timestamp="2024-01-15"
        )
        
        reply_dict = reply.to_dict()
        
        assert reply_dict["reply_number"] == "1"
        assert reply_dict["content"] == "Test content"
        assert reply_dict["author"]["username"] == "test"
        assert reply_dict["upvotes"] == 3
    
    def test_reply_to_markdown(self):
        """Test converting Reply to markdown."""
        author = Author(
            name="John Doe",
            username="johndoe",
            rank="5th in this Competition"
        )
        reply = Reply(
            reply_number="1",
            content="This is a test reply\nWith multiple lines",
            author=author,
            upvotes=10,
            timestamp="2024-01-15 10:30:00"
        )
        
        markdown = reply.to_markdown()
        
        assert "### Reply 1" in markdown
        assert "John Doe (@johndoe)" in markdown
        assert "5th in this Competition" in markdown
        assert "Upvotes: 10" in markdown
        assert "This is a test reply" in markdown
        assert "With multiple lines" in markdown


class TestDiscussion:
    """Test Discussion model."""
    
    def test_discussion_creation(self):
        """Test creating a Discussion instance."""
        author = Author(name="Host", username="host")
        discussion = Discussion(
            title="Test Discussion",
            url="https://www.kaggle.com/competitions/test/discussion/123",
            main_content="Main discussion content",
            main_author=author,
            main_upvotes=20,
            replies=[],
            total_replies=0,
            extraction_time=datetime.now().isoformat()
        )
        
        assert discussion.title == "Test Discussion"
        assert discussion.main_author.username == "host"
        assert discussion.main_upvotes == 20
        assert discussion.total_replies == 0
    
    def test_discussion_with_replies(self):
        """Test Discussion with replies."""
        main_author = Author(name="Host", username="host")
        reply_author = Author(name="User", username="user")
        
        reply = Reply(
            reply_number="1",
            content="Reply content",
            author=reply_author,
            upvotes=5,
            timestamp="2024-01-15"
        )
        
        discussion = Discussion(
            title="Test Discussion",
            url="https://example.com",
            main_content="Main content",
            main_author=main_author,
            main_upvotes=10,
            replies=[reply],
            total_replies=1,
            extraction_time=datetime.now().isoformat()
        )
        
        assert len(discussion.replies) == 1
        assert discussion.replies[0].author.username == "user"
        assert discussion.total_replies == 1
    
    def test_discussion_statistics(self):
        """Test getting discussion statistics."""
        main_author = Author(name="Host", username="host")
        reply1_author = Author(name="User1", username="user1")
        reply2_author = Author(name="User2", username="user2")
        
        sub_reply = Reply(
            reply_number="1.1",
            content="Sub reply",
            author=reply2_author,
            upvotes=3,
            timestamp="2024-01-15"
        )
        
        reply1 = Reply(
            reply_number="1",
            content="Reply 1",
            author=reply1_author,
            upvotes=5,
            timestamp="2024-01-15",
            sub_replies=[sub_reply]
        )
        
        reply2 = Reply(
            reply_number="2",
            content="Reply 2",
            author=reply2_author,
            upvotes=7,
            timestamp="2024-01-15"
        )
        
        discussion = Discussion(
            title="Test",
            url="https://example.com",
            main_content="Content",
            main_author=main_author,
            main_upvotes=10,
            replies=[reply1, reply2],
            total_replies=3,
            extraction_time=datetime.now().isoformat()
        )
        
        stats = discussion.get_statistics()
        
        assert stats["total_comments"] == 3
        assert stats["unique_authors"] == 3  # host, user1, user2
        assert stats["total_upvotes"] == 25  # 10 + 5 + 3 + 7
        assert stats["max_hierarchy_depth"] == 2  # Main -> Reply -> Sub-reply
        assert stats["top_level_replies"] == 2
        assert stats["nested_replies"] == 1
    
    def test_discussion_to_json(self):
        """Test converting Discussion to JSON."""
        author = Author(name="Host", username="host")
        discussion = Discussion(
            title="Test",
            url="https://example.com",
            main_content="Content",
            main_author=author,
            main_upvotes=5,
            replies=[],
            total_replies=0,
            extraction_time="2024-01-15T10:30:00"
        )
        
        json_str = discussion.to_json()
        
        assert '"title": "Test"' in json_str
        assert '"main_upvotes": 5' in json_str
        assert '"username": "host"' in json_str
    
    def test_discussion_to_markdown(self):
        """Test converting Discussion to markdown."""
        author = Author(
            name="Host",
            username="host",
            badges=["Competition Host"]
        )
        discussion = Discussion(
            title="Test Discussion",
            url="https://example.com",
            main_content="This is the main content",
            main_author=author,
            main_upvotes=15,
            replies=[],
            total_replies=0,
            extraction_time="2024-01-15T10:30:00"
        )
        
        markdown = discussion.to_markdown()
        
        assert "# Test Discussion" in markdown
        assert "Host (@host)" in markdown
        assert "Competition Host" in markdown
        assert "Upvotes: 15" in markdown
        assert "This is the main content" in markdown
        assert "https://example.com" in markdown