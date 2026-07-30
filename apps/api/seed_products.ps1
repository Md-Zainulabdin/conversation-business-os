$base = "http://localhost:8000"

# Register + login to get token
$body = @{
  email = "admin@cbo.local"
  password = "password123"
  name = "Store Owner"
} | ConvertTo-Json

$reg = curl.exe -s -X POST "$base/auth/register" -H "Content-Type: application/json" -d $body
$login = curl.exe -s -X POST "$base/auth/login" -H "Content-Type: application/json" -d $body
$token = ($login | ConvertFrom-Json).access_token

$auth = "Authorization: Bearer $token"

# Create categories
$categories = @("Grains", "Beverages", "Dairy", "Oils & Ghee", "Household", "Snacks")
foreach ($cat in $categories) {
  $catBody = @{ name = $cat } | ConvertTo-Json
  curl.exe -s -X POST "$base/categories" -H "Content-Type: application/json" -H $auth -d $catBody
}

# Create products from dummy.json
$products = @(
  @{ name = "Super Basmati Rice 5kg"; sku = "GRN-RICE-05"; category = "Grains"; unit = "Pack"; purchase_price = 1250; selling_price = 1600; stock_quantity = 45; minimum_stock = 10 },
  @{ name = "Coca Cola 1.5L Bottle"; sku = "BEV-COKE-15"; category = "Beverages"; unit = "Piece"; purchase_price = 120; selling_price = 180; stock_quantity = 120; minimum_stock = 25 },
  @{ name = "Full Cream Milk 1L"; sku = "DRY-MILK-01"; category = "Dairy"; unit = "Litre"; purchase_price = 110; selling_price = 150; stock_quantity = 8; minimum_stock = 15 },
  @{ name = "Whole Wheat Flour 10kg"; sku = "GRN-FLOU-10"; category = "Grains"; unit = "Pack"; purchase_price = 800; selling_price = 1120; stock_quantity = 30; minimum_stock = 10 },
  @{ name = "Refined Cooking Oil 3L"; sku = "OIL-COOK-03"; category = "Oils & Ghee"; unit = "Litre"; purchase_price = 650; selling_price = 900; stock_quantity = 5; minimum_stock = 12 },
  @{ name = "Lipton Yellow Label Tea 500g"; sku = "BEV-TEA-500"; category = "Beverages"; unit = "Pack"; purchase_price = 420; selling_price = 600; stock_quantity = 60; minimum_stock = 15 },
  @{ name = "White Refined Sugar 5kg"; sku = "GRN-SUGA-05"; category = "Grains"; unit = "Pack"; purchase_price = 480; selling_price = 650; stock_quantity = 85; minimum_stock = 20 },
  @{ name = "Unsalted Butter 200g"; sku = "DRY-BUTT-20"; category = "Dairy"; unit = "Piece"; purchase_price = 200; selling_price = 280; stock_quantity = 18; minimum_stock = 10 },
  @{ name = "Dishwashing Liquid 750ml"; sku = "HSH-DISH-75"; category = "Household"; unit = "Bottle"; purchase_price = 250; selling_price = 370; stock_quantity = 4; minimum_stock = 8 },
  @{ name = "Potato Chips Salted 150g"; sku = "SNK-CHIP-15"; category = "Snacks"; unit = "Pack"; purchase_price = 80; selling_price = 140; stock_quantity = 110; minimum_stock = 30 }
)

foreach ($p in $products) {
  $pBody = $p | ConvertTo-Json
  $result = curl.exe -s -X POST "$base/products" -H "Content-Type: application/json" -H $auth -d $pBody
  Write-Output "Created: $($p.name)"
}
