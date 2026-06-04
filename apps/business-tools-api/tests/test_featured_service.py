from business_tools.featured.service import (
    apply_featured_plan,
    build_featured_plan,
    list_suppliers,
    resolve_featured_category,
)


class FakeFeaturedClient:
    def __init__(self, categories, products, current_featured=None, fail_on=None):
        self.categories = categories
        self.products = products
        self.current_featured = current_featured if current_featured is not None else []
        self.fail_on = fail_on
        self.updates = []

    def get_all_categories(self):
        return self.categories

    def search_enabled_products(self, extra_params=None):
        return self.products

    def get_products_by_attribute(self, attribute_name, attribute_value):
        return [
            product
            for product in self.products
            if any(
                attribute.get("name") == attribute_name and attribute.get("value") == attribute_value
                for attribute in product.get("attributes", [])
            )
        ]

    def get_products_by_category(self, category_id):
        return self.current_featured

    def update_product_category_ids(self, product_id, category_ids):
        if product_id == self.fail_on:
            raise RuntimeError("update failed")
        self.updates.append((product_id, category_ids))


def product(product_id, sku, name, supplier, category_ids, default_category_id=10):
    return {
        "id": product_id,
        "sku": sku,
        "name": name,
        "enabled": True,
        "categoryIds": category_ids,
        "defaultCategoryId": default_category_id,
        "attributes": [{"name": "Brand", "value": supplier}],
    }


def test_list_suppliers_counts_enabled_products_by_attribute():
    client = FakeFeaturedClient(
        categories=[],
        products=[
            product(1, "A1", "Alpha", "Acme", [10]),
            product(2, "A2", "Beta", "Acme", [10]),
            product(3, "B1", "Gamma", "BeeCo", [11]),
        ],
    )

    suppliers = list_suppliers(client, "Brand")

    assert [(supplier.name, supplier.product_count) for supplier in suppliers] == [
        ("Acme", 2),
        ("BeeCo", 1),
    ]


def test_resolve_featured_category_uses_exact_name_match():
    client = FakeFeaturedClient(
        categories=[
            {"id": 98, "name": "Homepage"},
            {"id": 99, "name": "Featured Products"},
        ],
        products=[],
    )

    category = resolve_featured_category(client, "featured products")

    assert category.id == 99
    assert category.name == "Featured Products"


def test_resolve_featured_category_rejects_duplicate_names():
    client = FakeFeaturedClient(
        categories=[
            {"id": 98, "name": "Featured Products"},
            {"id": 99, "name": "featured products"},
        ],
        products=[],
    )

    try:
        resolve_featured_category(client, "Featured Products")
    except ValueError as exc:
        assert "Multiple categories" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_build_featured_plan_adds_supplier_products_and_removes_unselected_featured_products():
    featured_id = 99
    add = product(1, "ADD", "Add me", "Acme", [10])
    keep = product(2, "KEEP", "Keep me", "Acme", [10, featured_id])
    remove = product(3, "OLD", "Old featured", "Other", [11, featured_id], default_category_id=11)
    client = FakeFeaturedClient(
        categories=[{"id": featured_id, "name": "Featured Products"}],
        products=[add, keep],
        current_featured=[keep, remove],
    )

    plan = build_featured_plan(
        "Acme",
        client,
        supplier_attribute_name="Brand",
        featured_category_name="Featured Products",
    )

    assert [product.sku for product in plan.products_to_add] == ["ADD"]
    assert [product.sku for product in plan.products_to_keep] == ["KEEP"]
    assert [product.sku for product in plan.products_to_remove] == ["OLD"]


def test_build_featured_plan_honours_selected_product_ids():
    featured_id = 99
    add = product(1, "ADD", "Add me", "Acme", [10])
    skip = product(2, "SKIP", "Skip me", "Acme", [10])
    client = FakeFeaturedClient(
        categories=[{"id": featured_id, "name": "Featured Products"}],
        products=[add, skip],
        current_featured=[],
    )

    plan = build_featured_plan(
        "Acme",
        client,
        supplier_attribute_name="Brand",
        featured_category_name="Featured Products",
        selected_product_ids={1},
    )

    assert [product.sku for product in plan.selected_products] == ["ADD"]
    assert [product.sku for product in plan.products_to_add] == ["ADD"]


def test_apply_featured_plan_updates_only_category_ids():
    featured_id = 99
    add = product(1, "ADD", "Add me", "Acme", [10], default_category_id=10)
    remove = product(3, "OLD", "Old featured", "Other", [11, featured_id], default_category_id=11)
    client = FakeFeaturedClient(
        categories=[{"id": featured_id, "name": "Featured Products"}],
        products=[add],
        current_featured=[remove],
    )
    plan = build_featured_plan(
        "Acme",
        client,
        supplier_attribute_name="Brand",
        featured_category_name="Featured Products",
    )

    result = apply_featured_plan(plan, client)

    assert result.partial_failure is False
    assert client.updates == [(3, [11]), (1, [10, 99])]


def test_apply_featured_plan_preserves_non_featured_categories_from_category_ids():
    featured_id = 99
    current = {
        "id": 3,
        "sku": "OLD",
        "name": "Old featured",
        "enabled": True,
        "categoryIds": [11, featured_id],
        "defaultCategoryId": 11,
        "categories": [{"id": featured_id, "name": "Featured Products", "enabled": False}],
        "attributes": [{"name": "Brand", "value": "Other"}],
    }
    client = FakeFeaturedClient(
        categories=[{"id": featured_id, "name": "Featured Products", "enabled": False}],
        products=[],
        current_featured=[current],
    )
    plan = build_featured_plan(
        "Acme",
        client,
        supplier_attribute_name="Brand",
        featured_category_name="Featured Products",
        selected_product_ids=set(),
    )

    result = apply_featured_plan(plan, client)

    assert result.partial_failure is False
    assert client.updates == [(3, [11])]


def test_apply_featured_plan_stops_on_failure():
    featured_id = 99
    add = product(1, "ADD", "Add me", "Acme", [10])
    client = FakeFeaturedClient(
        categories=[{"id": featured_id, "name": "Featured Products"}],
        products=[add],
        current_featured=[],
        fail_on=1,
    )
    plan = build_featured_plan(
        "Acme",
        client,
        supplier_attribute_name="Brand",
        featured_category_name="Featured Products",
    )

    result = apply_featured_plan(plan, client)

    assert result.partial_failure is True
    assert result.updates[0].success is False
    assert client.updates == []
