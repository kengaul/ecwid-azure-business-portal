from business_tools.vat.service import apply_vat_plan, build_vat_plan, list_categories


class FakeVatClient:
    def __init__(self, categories, products, fail_on=None):
        self.categories = categories
        self.products = products
        self.fail_on = fail_on
        self.updates = []

    def get_all_categories(self):
        return self.categories

    def get_products_by_category(self, category_id):
        return self.products

    def update_product_tax_class(self, product_id, tax_class_code):
        if product_id == self.fail_on:
            raise RuntimeError("update failed")
        self.updates.append((product_id, tax_class_code))


def test_list_categories_sorts_by_name():
    client = FakeVatClient(
        categories=[
            {"id": 2, "name": "Books", "enabled": True},
            {"id": 1, "name": "Accessories", "enabled": False},
        ],
        products=[],
    )

    categories = list_categories(client)

    assert [(category.id, category.name) for category in categories] == [
        (1, "Accessories"),
        (2, "Books"),
    ]


def test_build_vat_plan_finds_products_not_already_zero_rated():
    client = FakeVatClient(
        categories=[{"id": 10, "name": "Books", "enabled": True}],
        products=[
            {
                "id": 1,
                "sku": "STD",
                "name": "Standard",
                "enabled": True,
                "tax": {"taxable": True, "defaultLocationIncludedTaxRate": 20, "taxClassCode": "default"},
            },
            {
                "id": 2,
                "sku": "ZERO",
                "name": "Zero",
                "enabled": True,
                "tax": {"taxable": True, "defaultLocationIncludedTaxRate": 0, "taxClassCode": "zero"},
            },
        ],
    )

    plan = build_vat_plan(10, client)

    assert [product.sku for product in plan.products_to_update] == ["STD"]
    assert [product.sku for product in plan.already_zero_rated] == ["ZERO"]


def test_build_vat_plan_limits_products_to_selected_ids():
    client = FakeVatClient(
        categories=[{"id": 10, "name": "Books", "enabled": True}],
        products=[
            {
                "id": 1,
                "sku": "KEEP",
                "name": "Keep",
                "enabled": True,
                "tax": {"taxable": True, "defaultLocationIncludedTaxRate": 20, "taxClassCode": "default"},
            },
            {
                "id": 2,
                "sku": "SKIP",
                "name": "Skip",
                "enabled": True,
                "tax": {"taxable": True, "defaultLocationIncludedTaxRate": 20, "taxClassCode": "default"},
            },
        ],
    )

    plan = build_vat_plan(10, client, selected_product_ids={1})

    assert [product.sku for product in plan.products_to_update] == ["KEEP"]


def test_build_vat_plan_rejects_missing_category():
    client = FakeVatClient(categories=[], products=[])

    try:
        build_vat_plan(999, client)
    except ValueError as exc:
        assert "999" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_apply_vat_plan_sets_tax_class_to_zero():
    client = FakeVatClient(
        categories=[{"id": 10, "name": "Books", "enabled": True}],
        products=[
            {
                "id": 1,
                "sku": "STD",
                "name": "Standard",
                "enabled": True,
                "tax": {"taxable": True, "defaultLocationIncludedTaxRate": 20, "taxClassCode": "default"},
            }
        ],
    )
    plan = build_vat_plan(10, client)

    result = apply_vat_plan(plan, client)

    assert result.partial_failure is False
    assert client.updates == [(1, "zero")]


def test_apply_vat_plan_stops_on_failure():
    client = FakeVatClient(
        categories=[{"id": 10, "name": "Books", "enabled": True}],
        products=[
            {
                "id": 1,
                "sku": "STD",
                "name": "Standard",
                "enabled": True,
                "tax": {"taxable": True, "defaultLocationIncludedTaxRate": 20, "taxClassCode": "default"},
            },
            {
                "id": 2,
                "sku": "RED",
                "name": "Reduced",
                "enabled": True,
                "tax": {"taxable": True, "defaultLocationIncludedTaxRate": 5, "taxClassCode": "gb-reduced"},
            },
        ],
        fail_on=1,
    )
    plan = build_vat_plan(10, client)

    result = apply_vat_plan(plan, client)

    assert result.partial_failure is True
    assert result.updates[0].success is False
    assert client.updates == []
