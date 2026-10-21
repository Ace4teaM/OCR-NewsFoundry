import Image from "next/image";
import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1>Heading 3XL</h1>
        <p>This is a paragraph under the heading.</p>
        <h2>Heading 2XL</h2>
        <p>This is another paragraph under the second heading.</p>
        <h3>Heading XL</h3>
        <p>This is a paragraph under the third heading.</p>
        <h4>Heading L</h4>
        <p>This is a paragraph under the fourth heading.</p>
        <h5>Heading M</h5>
        <p>This is a paragraph under the fifth heading.</p>
        <h6>Heading S</h6>
        <p>This is a paragraph under the sixth heading.</p>
      </main>
    </div>
  );
}
