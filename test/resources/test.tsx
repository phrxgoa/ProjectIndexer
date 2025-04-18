// Sample TSX file for testing the parser

import React, { useState, useEffect } from "react";
import { SampleClass } from "./test"; // Assuming test.ts exports SampleClass

// Interface for component props
interface MyComponentProps {
  title: string;
  initialCount?: number;
}

// Functional component with hooks and JSX
const MyComponent: React.FC<MyComponentProps> = ({
  title,
  initialCount = 0,
}) => {
  const [count, setCount] = useState<number>(initialCount);
  const [data, setData] = useState<SampleClass | null>(null);

  useEffect(() => {
    // Simulate fetching data
    const instance = new SampleClass("TSX Component", count);
    setData(instance);
    console.log("Component mounted or count updated");

    return () => {
      console.log("Component will unmount or count changed");
    };
  }, [count]); // Dependency array

  const increment = () => setCount((prevCount) => prevCount + 1);
  const decrement = () => setCount((prevCount) => prevCount - 1);

  return (
    <div
      className="my-component"
      style={{ border: "1px solid #ccc", padding: "10px" }}
    >
      <h1>{title}</h1>
      <p>Current Count: {count}</p>
      {data && <p>Data Name: {data.name}</p>}
      <button onClick={increment}>Increment</button>
      <button onClick={decrement}>Decrement</button>
      {/* Self-closing tag */}
      <hr />
      {/* Fragment */}
      <>
        <p>Fragment content</p>
      </>
      {/* Conditional rendering */}
      {count > 5 && <p style={{ color: "green" }}>Count is greater than 5!</p>}
    </div>
  );
};

// Another simple component
function SimpleDiv() {
  return <div>Just a simple div.</div>;
}

// Exporting the component
export default MyComponent;
export { SimpleDiv };

// Top-level variable using JSX type
let element: JSX.Element = <MyComponent title="Test Component" />;
