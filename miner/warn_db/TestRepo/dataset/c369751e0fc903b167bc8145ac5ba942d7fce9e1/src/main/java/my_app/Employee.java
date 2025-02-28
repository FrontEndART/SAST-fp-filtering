package my_app;

public class Employee{
	public static int WORKING_HOURS = 8;
	public static int AVERAGE_BREAK = 20;
    private String[] hobbies;
    public Date birthDate;
    
    public Employee(){
		hobbies = new String[]{};
		birthDate = new Date();
	}
	
    public Date getBirthDate()
    {return(birthDate);}
    
    public void setBirthDate(final Date birthDate)
    {this.birthDate = birthDate;}
	
    String[] getHobbies(){ return hobbies;}
	
    void setHobbies(String[] hobbies){ this.hobbies = hobbies;}
}

class Date{
	private int year, month, day;
	
    public Date() {
        year = 1010;
        month = 10;
        day = 10;
    }
	
	@Override
    public String toString() {
        return this.year + "." + this.month + "." + this.day + ".";
    }
}

