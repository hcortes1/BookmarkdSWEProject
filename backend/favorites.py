# backend/favorites.py
import psycopg2.extras
from backend.db import get_conn
from typing import List, Dict, Any, Optional


def get_user_favorites(user_id: int) -> Dict[str, List[int]]:
    """Get user's favorite authors and books"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT favorite_authors, favorite_books
                FROM users
                WHERE user_id = %s
            """, (user_id,))
            
            result = cur.fetchone()
            if result:
                return {
                    'favorite_authors': result['favorite_authors'] or [],
                    'favorite_books': result['favorite_books'] or []
                }
            return {'favorite_authors': [], 'favorite_books': []}
    except Exception as e:
        print(f"Error getting user favorites: {e}")
        return {'favorite_authors': [], 'favorite_books': []}


def is_author_favorited(user_id: int, author_id: int) -> bool:
    """Check if an author is in user's favorites"""
    favorites = get_user_favorites(user_id)
    return author_id in favorites['favorite_authors']


def is_book_favorited(user_id: int, book_id: int) -> bool:
    """Check if a book is in user's favorites"""
    favorites = get_user_favorites(user_id)
    return book_id in favorites['favorite_books']


def toggle_author_favorite(user_id: int, author_id: int) -> Dict[str, Any]:
    """Add or remove an author from user's favorites"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get current favorites
            favorites = get_user_favorites(user_id)
            favorite_authors = favorites['favorite_authors']
            
            if author_id in favorite_authors:
                # Remove from favorites
                favorite_authors.remove(author_id)
                action = 'removed'
            else:
                # Add to favorites
                favorite_authors.append(author_id)
                action = 'added'
            
            # Update database
            cur.execute("""
                UPDATE users 
                SET favorite_authors = %s
                WHERE user_id = %s
            """, (favorite_authors, user_id))
            
            conn.commit()
            
            return {
                'success': True,
                'action': action,
                'is_favorited': author_id in favorite_authors,
                'message': f"Author {action} {'to' if action == 'added' else 'from'} favorites"
            }
            
    except Exception as e:
        print(f"Error toggling author favorite: {e}")
        return {
            'success': False,
            'action': None,
            'is_favorited': False,
            'message': f"Error updating favorites: {str(e)}"
        }


def toggle_book_favorite(user_id: int, book_id: int) -> Dict[str, Any]:
    """Add or remove a book from user's favorites"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get current favorites
            favorites = get_user_favorites(user_id)
            favorite_books = favorites['favorite_books']
            
            if book_id in favorite_books:
                # Remove from favorites
                favorite_books.remove(book_id)
                action = 'removed'
            else:
                # Add to favorites
                favorite_books.append(book_id)
                action = 'added'
            
            # Update database
            cur.execute("""
                UPDATE users 
                SET favorite_books = %s
                WHERE user_id = %s
            """, (favorite_books, user_id))
            
            conn.commit()
            
            return {
                'success': True,
                'action': action,
                'is_favorited': book_id in favorite_books,
                'message': f"Book {action} {'to' if action == 'added' else 'from'} favorites"
            }
            
    except Exception as e:
        print(f"Error toggling book favorite: {e}")
        return {
            'success': False,
            'action': None,
            'is_favorited': False,
            'message': f"Error updating favorites: {str(e)}"
        }


def get_favorite_authors(user_id: int) -> List[Dict[str, Any]]:
    """Get detailed information about user's favorite authors"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT a.author_id, a.name, a.bio, a.birth_date, a.death_date, 
                       a.nationality, a.author_image_url
                FROM authors a
                JOIN users u ON a.author_id = ANY(u.favorite_authors)
                WHERE u.user_id = %s
                ORDER BY a.name
            """, (user_id,))
            
            results = cur.fetchall()
            return [dict(result) for result in results]
    except Exception as e:
        print(f"Error getting favorite authors: {e}")
        return []


def get_favorite_books(user_id: int) -> List[Dict[str, Any]]:
    """Get detailed information about user's favorite books"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT b.book_id, b.title, b.isbn, b.genre, b.release_date, 
                       b.description, b.cover_url, b.author_id,
                       a.name as author_name
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                JOIN users u ON b.book_id = ANY(u.favorite_books)
                WHERE u.user_id = %s
                ORDER BY b.title
            """, (user_id,))
            
            results = cur.fetchall()
            return [dict(result) for result in results]
    except Exception as e:
        print(f"Error getting favorite books: {e}")
        return []