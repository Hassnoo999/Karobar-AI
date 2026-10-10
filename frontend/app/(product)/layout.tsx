import { ProductShell } from "@/components/product/ProductShell";
import { ProductDataProvider } from "@/components/product/useProductData";

export default function ProductLayout({ children }: { children: React.ReactNode }) {
  return <ProductDataProvider><ProductShell>{children}</ProductShell></ProductDataProvider>;
}
