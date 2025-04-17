// Sample TypeScript file for testing the parser

import { AnotherClass } from "./another-module";
import * as fs from "fs";

// Simple interface
interface Person {
  name: string;
  age: number;
  greet?(): void; // Optional method
}

// Enum definition
export enum Color {
  Red,
  Green,
  Blue = 5, // Explicit value
}

// Class definition
class SampleClass extends AnotherClass implements Person {
  public name: string;
  readonly age: number;
  private secret: string;
  protected status: Color;

  constructor(name: string, age: number) {
    super();
    this.name = name;
    this.age = age;
    this.secret = "shhh";
    this.status = Color.Green;
  }

  // Public method
  public greet(): void {
    console.log(
      `Hello, my name is ${this.name} and I am ${this.age} years old.`
    );
  }

  // Private method
  private revealSecret(): string {
    return this.secret;
  }

  // Static method
  static createDefault(): SampleClass {
    return new SampleClass("Default", 0);
  }

  // Async method
  async loadData(path: string): Promise<string> {
    return new Promise((resolve, reject) => {
      fs.readFile(path, "utf8", (err, data) => {
        if (err) {
          reject(err);
        } else {
          resolve(data);
        }
      });
    });
  }
}

// Top-level function
function add(x: number, y: number): number {
  return x + y;
}

// Arrow function
const multiply = (a: number, b: number): number => a * b;

// Exporting variables
export const PI = 3.14159;
export let version = "1.0.0";

// Type alias
type StringOrNumber = string | number;

let value: StringOrNumber = "hello";
value = 123;

// Using the enum
let myColor: Color = Color.Blue;

// Using the class
const personInstance = new SampleClass("Alice", 30);
personInstance.greet();
const defaultPerson = SampleClass.createDefault();

console.log(add(5, 3));
console.log(multiply(4, 6));
console.log(`Color: ${Color[myColor]}, Value: ${myColor}`);
