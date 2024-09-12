"""
Chat Session Seeder

Purpose:
This script downloads a Google Sheet (publicly accessible) as a CSV file and
seeds the data into the database using SQLAlchemy. The script:
1. Downloads the Google Sheet data in CSV format.
2. Reads the CSV file into a pandas DataFrame.
3. Seeds the data into the database by creating or updating records.
4. Deletes the CSV file after seeding to clean up the production environment.

Usage:
1. Ensure the Google Sheet is publicly accessible.
2. Provide the Google Sheet ID when prompted.
3. Run the script in the production environment.
"""

import os
import requests
import pandas as pd
from sqlmodel import Session, select
from core.database import engine
from models import (
    User,
    User_Properties,
    Client,
    Client_Properties,
    Chat_Session,
)
from seeder.user import ValidatePhoneNumber


def download_csv_from_google_sheet(sheet_id: str):
    # Construct the CSV export URL from the Google Sheet ID
    csv_url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    )

    # Download the CSV file from the Google Sheet
    try:
        response = requests.get(csv_url)
        response.raise_for_status()

        csv_filename = f"./tmp/sources/{sheet_id}.csv"
        os.makedirs(os.path.dirname(csv_filename), exist_ok=True)
        with open(csv_filename, "wb") as f:
            f.write(response.content)

        print(f"CSV file successfully downloaded as {csv_filename}.")
        return csv_filename

    except requests.exceptions.RequestException as e:
        print(f"Failed to download the CSV file: {e}")
        return None


def seed_database(session: Session, csv_filepath: str):
    # Read the CSV file into a pandas DataFrame
    try:
        data = pd.read_csv(csv_filepath)

        for _, row in data.iterrows():
            # Process Client
            client_phone_number = row["client_phone_number"]
            client_name = row["client_name"]
            user_phone_number = row["linked_to_user_phone_number"]
            user_name = row["user_name"]

            # Check if Client already exists
            validated_client = ValidatePhoneNumber(
                phone_number=client_phone_number
            )
            client = session.exec(
                select(Client).where(
                    Client.phone_number == client_phone_number
                )
            ).first()
            if not client:
                client = Client(
                    phone_number=int(
                        "".join(
                            filter(str.isdigit, validated_client.phone_number)
                        )
                    )
                )
                session.add(client)

            # Create or update Client_Properties
            client_properties = session.exec(
                select(Client_Properties).where(
                    Client_Properties.client_id == client.id
                )
            ).first()
            if client_properties:
                client_properties.name = client_name
            else:
                client_properties = Client_Properties(
                    client_id=client.id, name=client_name
                )
                session.add(client_properties)

            # Check if User already exists
            user = session.exec(
                select(User).where(User.phone_number == user_phone_number)
            ).first()
            if not user:
                user = User(phone_number=user_phone_number)
                session.add(user)

            # Create or update User_Properties
            user_properties = session.exec(
                select(User_Properties).where(
                    User_Properties.user_id == user.id
                )
            ).first()
            if user_properties:
                user_properties.name = user_name
            else:
                user_properties = User_Properties(
                    user_id=user.id, name=user_name
                )
                session.add(user_properties)

            # Create Chat_Session
            chat_session = session.exec(
                select(Chat_Session).where(
                    (Chat_Session.user_id == user.id)
                    & (Chat_Session.client_id == client.id)
                )
            ).first()
            if not chat_session:
                chat_session = Chat_Session(
                    user_id=user.id, client_id=client.id
                )
                session.add(chat_session)

        # Commit all records to the database
        session.commit()
        print(f"Data from {csv_filepath} has been successfully seeded.")

    except Exception as e:
        print(f"Error occurred: {e}")
        session.rollback()
    finally:
        session.close()

    # Delete the CSV file after seeding
    try:
        os.remove(csv_filepath)
        print(f"CSV file {csv_filepath} has been successfully deleted.")
    except OSError as e:
        print(f"Error deleting file: {e}")


if __name__ == "__main__":
    session = Session(engine)

    # Ask the user for the Google Sheet ID
    google_sheet_id = input("Please enter the Google Sheet ID: ")

    # Download the CSV file from Google Sheets
    csv_filepath = download_csv_from_google_sheet(sheet_id=google_sheet_id)

    if csv_filepath:
        # Seed the database with the downloaded CSV file using pandas
        seed_database(session=session, csv_filepath=csv_filepath)
