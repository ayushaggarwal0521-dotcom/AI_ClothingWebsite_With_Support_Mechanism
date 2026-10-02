import uuid
from datetime import datetime, timedelta

from app.database import get_connection
from app.services.llm_service import create_llm_conversation


# ---------------------------------------------------------
# CREATE NEW CONVERSATION
# ---------------------------------------------------------

def create_conversation():

    # 1. Generate our conversation ID
    conversation_id = "CONV-" + str(uuid.uuid4())[:8]

    # 2. Create OpenAI conversation
    llm_conversation_id = create_llm_conversation()

    # 3. Connect to database
    connection = get_connection()
    cursor = connection.cursor()

    try:

        # 4. Create conversation
        cursor.execute("""
            INSERT INTO conversations (
                conversation_id,
                status,
                support_ticket_id,
                llm_conversation_id
            )
            VALUES (%s, %s, %s, %s)
            RETURNING
                conversation_id,
                status,
                support_ticket_id,
                llm_conversation_id,
                created_at,
                updated_at
        """, (
            conversation_id,
            "ACTIVE",
            None,
            llm_conversation_id
        ))

        conversation = cursor.fetchone()

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    # 5. Return conversation
    return {
        "success": True,
        "conversation_id": conversation[0],
        "status": conversation[1],
        "support_ticket_id": conversation[2],
        "llm_conversation_id": conversation[3],
        "created_at": conversation[4],
        "updated_at": conversation[5]
    }


# ---------------------------------------------------------
# GET CONVERSATION
# ---------------------------------------------------------

def get_conversation(conversation_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            conversation_id,
            status,
            support_ticket_id,
            llm_conversation_id,
            created_at,
            updated_at
        FROM conversations
        WHERE conversation_id = %s
    """, (conversation_id,))

    conversation = cursor.fetchone()

    cursor.close()
    connection.close()

    if conversation is None:
        return None

    return {
        "conversation_id": conversation[0],
        "status": conversation[1],
        "support_ticket_id": conversation[2],
        "llm_conversation_id": conversation[3],
        "created_at": conversation[4],
        "updated_at": conversation[5]
    }


# ---------------------------------------------------------
# CLOSE CONVERSATION
# ---------------------------------------------------------

def close_conversation(conversation_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE conversations
            SET
                status = 'CLOSED',
                updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = %s
              AND status = 'ACTIVE'
        """, (conversation_id,))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# ---------------------------------------------------------
# COUNT CUSTOMER MESSAGES
# ---------------------------------------------------------

def get_customer_message_count(conversation_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM messages
        WHERE conversation_id = %s
          AND sender_type = 'customer'
    """, (conversation_id,))

    count = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return count


# ---------------------------------------------------------
# SEND CUSTOMER MESSAGE
# ---------------------------------------------------------

def send_customer_message(
    conversation_id: str,
    message_text: str
):

    # -----------------------------------------------------
    # 1. Get conversation
    # -----------------------------------------------------

    conversation = get_conversation(conversation_id)

    if conversation is None:
        return {
            "success": False,
            "message": f"Conversation {conversation_id} does not exist."
        }

    # -----------------------------------------------------
    # 2. Make sure conversation is ACTIVE
    # -----------------------------------------------------

    if conversation["status"] != "ACTIVE":
        return {
            "success": False,
            "conversation_id": conversation_id,
            "status": conversation["status"],
            "message": (
                "This conversation is no longer active. "
                "Please start a new chat."
            )
        }

    # -----------------------------------------------------
    # 3. Check 30-minute inactivity
    # -----------------------------------------------------

    last_activity = conversation["updated_at"]
    current_time = datetime.now()

    inactivity_duration = current_time - last_activity

    if inactivity_duration >= timedelta(minutes=30):

        close_conversation(conversation_id)

        return {
            "success": False,
            "conversation_id": conversation_id,
            "status": "CLOSED",
            "message": (
                "This conversation expired because there was "
                "no activity for 30 minutes. Please start a new chat."
            )
        }

    # -----------------------------------------------------
    # 4. Count existing customer messages
    # -----------------------------------------------------

    customer_message_count = get_customer_message_count(
        conversation_id
    )

    # -----------------------------------------------------
    # 5. Check 20-message limit
    # -----------------------------------------------------

    if customer_message_count >= 20:

        connection = get_connection()
        cursor = connection.cursor()

        try:

            message_id = "MSG-" + str(uuid.uuid4())[:8]

            cursor.execute("""
                INSERT INTO messages (
                    message_id,
                    conversation_id,
                    sender_type,
                    message_text
                )
                VALUES (%s, %s, %s, %s)
                RETURNING
                    message_id,
                    conversation_id,
                    sender_type,
                    message_text,
                    message_time
            """, (
                message_id,
                conversation_id,
                "customer",
                message_text
            ))

            message = cursor.fetchone()

            cursor.execute("""
                UPDATE conversations
                SET
                    status = 'HUMAN_HANDOFF',
                    updated_at = CURRENT_TIMESTAMP
                WHERE conversation_id = %s
            """, (conversation_id,))

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

        return {
            "success": True,
            "conversation_id": conversation_id,
            "llm_conversation_id": conversation["llm_conversation_id"],
            "message_id": message[0],
            "message_text": message[3],
            "message_time": message[4],
            "status": "HUMAN_HANDOFF",
            "message_limit_reached": True,
            "customer_message_count": customer_message_count + 1,
            "support_message": (
                "You've reached the maximum number of messages for "
                "this chat. For further assistance, please contact "
                "our support team at support@yourstore.com or call "
                "+91 98765 43210. You can also start a new chat "
                "for a new query."
            )
        }

    # -----------------------------------------------------
    # 6. Normal message — save it
    # -----------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    try:

        message_id = "MSG-" + str(uuid.uuid4())[:8]

        cursor.execute("""
            INSERT INTO messages (
                message_id,
                conversation_id,
                sender_type,
                message_text
            )
            VALUES (%s, %s, %s, %s)
            RETURNING
                message_id,
                conversation_id,
                sender_type,
                message_text,
                message_time
        """, (
            message_id,
            conversation_id,
            "customer",
            message_text
        ))

        message = cursor.fetchone()

        # Update customer activity time
        cursor.execute("""
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = %s
        """, (conversation_id,))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    # -----------------------------------------------------
    # 7. Return result
    # -----------------------------------------------------

    return {
        "success": True,
        "conversation_id": conversation_id,
        "llm_conversation_id": conversation["llm_conversation_id"],
        "message_id": message[0],
        "sender_type": message[2],
        "message_text": message[3],
        "message_time": message[4],
        "status": "ACTIVE",
        "message_limit_reached": False,
        "customer_message_count": customer_message_count + 1
    }



def send_assistant_message(
    conversation_id: str,
    message_text: str
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        message_id = "MSG-" + str(uuid.uuid4())[:8]

        cursor.execute("""
            INSERT INTO messages (
                message_id,
                conversation_id,
                sender_type,
                message_text
            )
            VALUES (%s, %s, %s, %s)
            RETURNING
                message_id,
                conversation_id,
                sender_type,
                message_text,
                message_time
        """, (
            message_id,
            conversation_id,
            "assistant",
            message_text
        ))

        message = cursor.fetchone()

        cursor.execute("""
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = %s
        """, (conversation_id,))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    return {
        "success": True,
        "conversation_id": conversation_id,
        "message_id": message[0],
        "sender_type": message[2],
        "message_text": message[3],
        "message_time": message[4]
    }