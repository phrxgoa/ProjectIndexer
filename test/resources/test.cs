using System;

namespace TestProject
{
    public interface IExample
    {
        void InterfaceMethod();
    }

    public abstract class BaseClass
    {
        public abstract void AbstractMethod();
    }

    public class ExampleClass : BaseClass, IExample
    {
        private int _privateField;
        public string PublicProperty { get; set; }
        
        public const double PI = 3.14;
        
        public override void AbstractMethod()
        {
            Console.WriteLine("Implemented abstract method");
        }
        
        public void InterfaceMethod()
        {
            Console.WriteLine("Implemented interface method");
        }
        
        public string GetGreeting(string name)
        {
            return $"Hello, {name}";
        }
        
        private void PrivateMethod()
        {
            // Do something private
        }
    }

    public struct Point
    {
        public int X;
        public int Y;
    }

    public enum Status
    {
        Active,
        Inactive,
        Pending
    }
}