#!/usr/bin/env python3
"""
Test script for Concept API
"""

import sys

sys.path.append("/app")

import asyncio

from src.repositories.MDE.concept_repository import ConceptRepository
from src.repositories.MDE.metamodel_repository import MetamodelRepository
from src.services.MDE.concept_service import ConceptService

from src.database import get_db


async def test_concept_creation():
    """Test concept creation through service layer"""
    async for db in get_db():
        print("=" * 60)
        print("Testing Concept Creation")
        print("=" * 60)

        # Get a metamodel first
        metamodel_repo = MetamodelRepository(db)
        metamodels = await metamodel_repo.find_all()

        if not metamodels:
            print("❌ No metamodels found. Please create one first.")
            return

        metamodel = metamodels[0]
        print(f"\n📋 Using metamodel: {metamodel.name}")
        print(f"   ID: {metamodel.id}")
        print(f"   Current node count: {metamodel.node_count}")

        # Create concept service
        concept_repo = ConceptRepository(db)
        concept_service = ConceptService(concept_repo, metamodel_repo)

        # Create concept data (API format with metamodel_id and x/y)
        concept_data = {
            "name": "Product",
            "description": "Represents a product in the e-commerce system",
            "metamodel_id": metamodel.id,
            "x": 150.0,
            "y": 100.0,
        }

        print("\n📝 Creating concept:")
        print(f"   Name: {concept_data['name']}")
        print(f"   Description: {concept_data['description']}")
        print(f"   Metamodel ID: {concept_data['metamodel_id']}")
        print(f"   Position: ({concept_data['x']}, {concept_data['y']})")

        # Create concept through service
        try:
            concept = await concept_service.create(concept_data)
            print("\n✅ Concept created successfully!")
            print(f"   ID: {concept.id}")
            print(f"   Name: {concept.name}")
            print(f"   Description: {concept.description}")
            print(f"   Metamodel ID: {concept.metamodel_id}")
            print(f"   Position: ({concept.x}, {concept.y})")

            # Verify it's in the database
            concepts = await concept_repo.get_by_metamodel(metamodel.id)
            print(f"\n📊 Total concepts for this metamodel: {len(concepts)}")
            for c in concepts:
                print(f"   - {c.name} (id={c.id})")

            # Check metamodel node count was incremented
            updated_metamodel = await metamodel_repo.get_by_id(metamodel.id)
            print(
                f"\n📈 Metamodel node count: {metamodel.node_count} → {updated_metamodel.node_count}"
            )

        except Exception as e:
            print(f"\n❌ Error creating concept: {str(e)}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_concept_creation())
