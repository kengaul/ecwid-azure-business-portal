from business_tools.frontpage.service import apply_frontpage_plan, build_frontpage_plan


class FakeClient:
    def __init__(self, products, fail_on=None):
        self.products = products
        self.fail_on = fail_on
        self.updates = []

    def get_product_by_sku(self, sku):
        for product in self.products:
            if product["sku"] == sku:
                return product
        return None

    def get_all_enabled_products(self):
        return self.products

    def update_product_frontpage(self, product_id, priority):
        if product_id == self.fail_on:
            raise RuntimeError("update failed")
        self.updates.append((product_id, priority))


def test_build_frontpage_plan_skips_missing_and_removes_current_frontpage():
    client = FakeClient(
        [
            {"id": 1, "sku": "OLD", "name": "Old", "showOnFrontpage": 1},
            {"id": 2, "sku": "NEW", "name": "New", "showOnFrontpage": -1},
        ]
    )

    plan = build_frontpage_plan("NEW MISSING", client, max_skus=10)

    assert plan.valid_skus == ["NEW"]
    assert [warning.code for warning in plan.warnings] == ["not_found"]
    assert [product.sku for product in plan.removals] == ["OLD"]
    assert [(product.sku, product.target_priority) for product in plan.additions] == [("NEW", 1)]


def test_build_frontpage_plan_removes_current_frontpage_even_if_resubmitted():
    client = FakeClient(
        [
            {"id": 1, "sku": "KEEP", "name": "Keep", "showOnFrontpage": 1},
            {"id": 2, "sku": "NEW", "name": "New", "showOnFrontpage": -1},
        ]
    )

    plan = build_frontpage_plan("KEEP NEW", client, max_skus=10)

    assert [product.sku for product in plan.removals] == ["KEEP"]
    assert [(product.sku, product.target_priority) for product in plan.additions] == [
        ("KEEP", 1),
        ("NEW", 2),
    ]


def test_apply_frontpage_plan_removes_then_sets_priorities():
    client = FakeClient(
        [
            {"id": 1, "sku": "OLD", "name": "Old", "showOnFrontpage": 1},
            {"id": 2, "sku": "NEW", "name": "New", "showOnFrontpage": -1},
        ]
    )
    plan = build_frontpage_plan("NEW", client, max_skus=10)

    result = apply_frontpage_plan(plan, client)

    assert result.partial_failure is False
    assert client.updates == [(1, -1), (2, 1)]


def test_apply_frontpage_plan_stops_on_partial_failure():
    client = FakeClient(
        [
            {"id": 1, "sku": "OLD", "name": "Old", "showOnFrontpage": 1},
            {"id": 2, "sku": "NEW", "name": "New", "showOnFrontpage": -1},
        ],
        fail_on=1,
    )
    plan = build_frontpage_plan("NEW", client, max_skus=10)

    result = apply_frontpage_plan(plan, client)

    assert result.partial_failure is True
    assert client.updates == []
    assert result.updates[0].success is False
